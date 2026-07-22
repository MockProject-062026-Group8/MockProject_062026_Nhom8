document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const identifierInput = document.getElementById('identifier');
    const passwordInput = document.getElementById('password');
    const submitBtn = document.getElementById('submitBtn');
    const errorMessage = document.getElementById('errorMessage');

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    if (!loginForm || !identifierInput || !passwordInput || !submitBtn || !errorMessage) return;

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
        
        const identifier = identifierInput.value.trim();
        const password = passwordInput.value;
        
        if (!identifier || !password) {
            errorMessage.textContent = 'Identifier and password are required.';
            errorMessage.style.display = 'block';
            return;
        }

        submitBtn.disabled = true;
        submitBtn.textContent = 'Signing in...';
        
        const apiUrl = loginForm.getAttribute('data-api-url');
        const redirectUrl = loginForm.getAttribute('data-redirect-url');
        
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({ identifier, password })
            });

            let data;
            try {
                data = await response.json();
            } catch (err) {
                throw new Error('Invalid server response format.');
            }

            if (!response.ok) {
                throw new Error(data.detail || 'Invalid email/phone or password.');
            }
            
            if (!data.verification_token || !data.phone_number) {
                throw new Error('Invalid server response: missing token or phone number.');
            }
            
            sessionStorage.setItem('verification_token', data.verification_token);
            sessionStorage.setItem('masked_phone_number', data.phone_number);
            window.location.href = redirectUrl;
            
        } catch (error) {
            errorMessage.textContent = error.message || 'Network error. Please try again.';
            errorMessage.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Sign In';
        }
    });
});
