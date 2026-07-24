document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('residentTableBody');
    const loadingState = document.getElementById('loadingState');
    const errorState = document.getElementById('errorState');
    const emptyState = document.getElementById('emptyState');
    const countTotal = document.getElementById('countTotal');
    const countActive = document.getElementById('countActive');
    const countDischarged = document.getElementById('countDischarged');
    const countPending = document.getElementById('countPending');
    const recordCountText = document.getElementById('recordCountText');
    const prevBtn = document.getElementById('prevPageBtn');
    const nextBtn = document.getElementById('nextPageBtn');
    const pageIndicator = document.getElementById('pageIndicator');

    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const referralFilter = document.getElementById('referralFilter');

    const addResidentBtn = document.getElementById('addResidentBtn');
    const addResidentHelper = document.getElementById('addResidentHelper');

    let currentPage = 1;
    let searchTimeout = null;

    // Role-based visibility is deferred to shared integration after the exact role value is confirmed.

    function calculateAge(dobString) {
        if (!dobString) return '';
        const dob = new Date(dobString);
        const diffMs = Date.now() - dob.getTime();
        const ageDt = new Date(diffMs);
        return Math.abs(ageDt.getUTCFullYear() - 1970);
    }

    function getStatusBadgeNode(status) {
        const span = document.createElement('span');
        span.className = 'status-badge status-' + (status || '').toLowerCase();
        span.textContent = status || '';
        return span;
    }

    function renderTable(results) {
        tableBody.querySelectorAll('.resident-row').forEach(row => row.remove());
        if (results.length === 0) {
            emptyState.style.display = 'table-row';
            return;
        }
        emptyState.style.display = 'none';

        results.forEach(res => {
            const tr = document.createElement('tr');
            tr.className = 'resident-row';
            const age = calculateAge(res.date_of_birth);
            const dobAge = res.date_of_birth ? `${res.date_of_birth} (${age})` : 'N/A';

            const tdName = document.createElement('td');
            tdName.textContent = `${res.first_name} ${res.last_name}`;

            const tdRoom = document.createElement('td');
            tdRoom.textContent = res.room_number || 'N/A';

            const tdStatus = document.createElement('td');
            tdStatus.appendChild(getStatusBadgeNode(res.status));

            const tdDob = document.createElement('td');
            tdDob.textContent = dobAge;

            const tdPayer = document.createElement('td');
            tdPayer.textContent = res.payer_source || 'N/A';

            const tdReferral = document.createElement('td');
            tdReferral.textContent = res.referral_source || 'N/A';

            const tdAction = document.createElement('td');
            const viewBtn = document.createElement('a');
            viewBtn.className = 'btn btn-sm btn-secondary';
            viewBtn.textContent = 'View';
            viewBtn.href = `/residents/resident_details/${res.id}/`;
            tdAction.appendChild(viewBtn);

            tr.appendChild(tdName);
            tr.appendChild(tdRoom);
            tr.appendChild(tdStatus);
            tr.appendChild(tdDob);
            tr.appendChild(tdPayer);
            tr.appendChild(tdReferral);
            tr.appendChild(tdAction);

            tableBody.appendChild(tr);
        });
    }

    function fetchResidents() {
        loadingState.style.display = 'table-row';
        errorState.style.display = 'none';
        emptyState.style.display = 'none';
        tableBody.querySelectorAll('.resident-row').forEach(row => row.remove());

        const params = new URLSearchParams();
        params.append('page', currentPage);
        if (searchInput.value.trim()) params.append('search', searchInput.value.trim());
        if (statusFilter.value) params.append('status', statusFilter.value);
        if (referralFilter.value.trim()) params.append('referral_source', referralFilter.value.trim());
        params.append('ordering', '-created_at');

        const token = sessionStorage.getItem('access_token');
        const headers = { 'Content-Type': 'application/json' };
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        fetch(`/api/v1/residents/?${params.toString()}`, { headers })
            .then(res => {
                if (!res.ok) throw new Error('API Error');
                return res.json();
            })
            .then(data => {
                loadingState.style.display = 'none';

                countTotal.textContent = data.summary?.total || 0;
                countActive.textContent = data.summary?.active || 0;
                countDischarged.textContent = data.summary?.discharged || 0;
                countPending.textContent = data.summary?.pending || 0;

                recordCountText.textContent = `${data.count} residents \u00B7 sorted by Date Added (newest first)`;

                pageIndicator.textContent = `Page ${currentPage}`;
                prevBtn.disabled = !data.previous;
                nextBtn.disabled = !data.next;

                const uniqueReferrals = [...new Set((data.results || []).map(r => r.referral_source).filter(Boolean))];
                const referralList = document.getElementById('referralList');
                referralList.innerHTML = '';
                uniqueReferrals.forEach(ref => {
                    const opt = document.createElement('option');
                    opt.value = ref;
                    referralList.appendChild(opt);
                });

                renderTable(data.results || []);
            })
            .catch(err => {
                loadingState.style.display = 'none';
                errorState.style.display = 'table-row';
                console.error(err);
            });
    }

    searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            fetchResidents();
        }, 500);
    });

    statusFilter.addEventListener('change', () => {
        currentPage = 1;
        fetchResidents();
    });

    referralFilter.addEventListener('change', () => {
        currentPage = 1;
        fetchResidents();
    });

    prevBtn.addEventListener('click', () => {
        if (!prevBtn.disabled) {
            currentPage--;
            fetchResidents();
        }
    });

    nextBtn.addEventListener('click', () => {
        if (!nextBtn.disabled) {
            currentPage++;
            fetchResidents();
        }
    });

    fetchResidents();
});
