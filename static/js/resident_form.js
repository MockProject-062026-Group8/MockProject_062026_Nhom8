  // ---------- Photo upload preview ----------
  const photoUpload = document.getElementById('photoUpload');
  const photoInput = document.getElementById('photoInput');
  const photoPreview = document.getElementById('photoPreview');
  const photoPlaceholder = document.getElementById('photoPlaceholder');

  if (photoUpload) {
    photoUpload.addEventListener('click', () => photoInput.click());
    photoInput.addEventListener('change', () => {
      const file = photoInput.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = (e) => {
        photoPreview.src = e.target.result;
        photoPreview.style.display = 'block';
        photoPlaceholder.style.display = 'none';
      };
      reader.readAsDataURL(file);
    });
  }

  // ---------- Generic toggle helper ----------
  // fieldIds: các input/select sẽ được enable/disable theo trạng thái toggle
  function setupToggle(toggleId, statusTextId, fieldIds, offLabel, onLabel) {
    const toggle = document.getElementById(toggleId);
    const statusText = document.getElementById(statusTextId);
    if (!toggle || !statusText) return;
    
    toggle.addEventListener('change', () => {
      const isOn = toggle.checked;
      statusText.textContent = isOn ? onLabel : offLabel;
      fieldIds.forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.disabled = !isOn;
      });
    });
  }

  setupToggle('poaToggle', 'poaStatusText',
    ['poaFullName', 'poaType', 'poaRelationship', 'poaPhone', 'poaEffectiveDate', 'poaDocument'],
    'No', 'Yes');

  setupToggle('advDirectiveToggle', 'advDirectiveStatusText', [], 'No', 'Yes — On File');

  setupToggle('proxyToggle', 'proxyStatusText', ['proxyName'], 'No', 'Yes');

  // DNR toggle: đổi màu đỏ + text nhấn mạnh khi bật
  const dnrToggle = document.getElementById('dnrToggle');
  const dnrStatusText = document.getElementById('dnrStatusText');
  if (dnrToggle && dnrStatusText) {
    dnrToggle.addEventListener('change', () => {
      const isOn = dnrToggle.checked;
      dnrStatusText.textContent = isOn ? 'Yes — DNR Active' : 'No';
      dnrStatusText.classList.toggle('flag-status-critical', isOn);
    });
  }

  // ---------- Medicare Number field: chỉ thực sự cần khi Payer Source = Medicare ----------
  const payerSource = document.getElementById('payerSource');
  const medicareNumberGroup = document.getElementById('medicareNumberGroup');
  function toggleMedicareField() {
    if (medicareNumberGroup && payerSource) {
      medicareNumberGroup.style.display = payerSource.value === 'medicare' ? '' : 'none';
    }
  }
  if (payerSource) {
    payerSource.addEventListener('change', toggleMedicareField);
    toggleMedicareField();
  }

  // ---------- Duplicate name check khi blur Last Name ----------
  // Gợi ý: cần một Django view trả JSON {"exists": true/false} tại URL bên dưới.
  const lastNameInput = document.getElementById('id_last_name');
  const firstNameInput = document.getElementById('id_first_name');
  const duplicateWarning = document.getElementById('duplicateWarning');

  if (lastNameInput && firstNameInput && duplicateWarning) {
    lastNameInput.addEventListener('blur', async () => {
      const firstName = firstNameInput.value.trim();
      const lastName = lastNameInput.value.trim();
      if (!lastName) return;
      try {
        const url = `/residents/check-duplicate/?first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}`;
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        duplicateWarning.style.display = data.exists ? '' : 'none';
      } catch (err) {
        // Nếu endpoint chưa tồn tại, bỏ qua lỗi im lặng để không chặn người dùng
        console.warn('Duplicate check unavailable:', err);
      }
    });
  }

  // ---------- Inline validation khi bấm Save ----------
  const form = document.getElementById('residentForm');
  if (form) {
    form.addEventListener('submit', (e) => {
      let hasError = false;
      form.querySelectorAll('[required]').forEach((field) => {
        const group = field.closest('.form-group');
        const errorText = group ? group.querySelector('.error-text') : null;
        if (!field.value.trim()) {
          hasError = true;
          if (group) group.classList.add('has-error');
          if (errorText) errorText.textContent = 'This field is required.';
        } else {
          if (group) group.classList.remove('has-error');
          if (errorText) errorText.textContent = '';
        }
      });
      if (hasError) {
        e.preventDefault();
        const firstError = form.querySelector('.has-error');
        if (firstError) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }
