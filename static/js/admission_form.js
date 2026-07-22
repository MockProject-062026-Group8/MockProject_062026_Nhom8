document.addEventListener('DOMContentLoaded', function() {
  const admissionForm = document.getElementById('admissionForm');
  const errorBanner = document.getElementById('errorBanner');
  const btnConfirmAdmission = document.getElementById('btnConfirmAdmission');

  // Real-time Update for Order Accountability (A-21)
  const physicianInput = document.getElementById('physician');
  const physicianNpiInput = document.getElementById('physician_npi');
  const displayPhysicianName = document.getElementById('acc_physician');
  const displayPhysicianLicense = document.getElementById('acc_npi');
  const displayOrderDate = document.getElementById('acc_date');
  const orderDateInput = document.getElementById('order_date');

  function updateAccountability() {
    if(displayPhysicianName) displayPhysicianName.textContent = physicianInput.value || '(Pending)';
    if(displayOrderDate && orderDateInput) displayOrderDate.textContent = orderDateInput.value || '(Pending)';
    
    const npiValue = physicianNpiInput.value.trim();
    if (npiValue) {
      if(displayPhysicianLicense) displayPhysicianLicense.textContent = npiValue;
    } else {
      if(displayPhysicianLicense) displayPhysicianLicense.textContent = '(Pending)';
    }
  }

  if(physicianInput) physicianInput.addEventListener('input', updateAccountability);
  if(physicianNpiInput) physicianNpiInput.addEventListener('input', updateAccountability);
  if(orderDateInput) orderDateInput.addEventListener('input', updateAccountability);

  // Verification Method Toggle
  const radioMethods = document.querySelectorAll('input[name="verification_method"]');
  const uploadContainer = document.getElementById('upload_container');
  
  radioMethods.forEach(radio => {
    radio.addEventListener('change', function() {
      if (this.value === 'upload') {
        uploadContainer.style.display = 'block';
      } else {
        uploadContainer.style.display = 'none';
      }
    });
  });

  // Clear File Logic
  const fileInput = document.getElementById('consent_file');
  const btnClearFile = document.getElementById('btnClearFile');
  if (fileInput && btnClearFile) {
    fileInput.addEventListener('change', function() {
      if (this.files.length > 0) {
        btnClearFile.style.display = 'block';
      } else {
        btnClearFile.style.display = 'none';
      }
    });

    btnClearFile.addEventListener('click', function(e) {
      e.preventDefault();
      fileInput.value = '';
      this.style.display = 'none';
    });
  }
  // Signature Canvas Logic
  const signatureModal = document.getElementById('signatureModal');
  const signatureCanvas = document.getElementById('signatureCanvas');
  const btnClearSignature = document.getElementById('btnClearSignature');
  const btnCancelSignature = document.getElementById('btnCancelSignature');
  const btnSaveSignature = document.getElementById('btnSaveSignature');
  
  let ctx = signatureCanvas ? signatureCanvas.getContext('2d') : null;
  let isDrawing = false;
  let hasSigned = false;
  let signatureData = null;

  if (signatureCanvas) {
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#000';

    function startPosition(e) {
      isDrawing = true;
      draw(e);
    }

    function endPosition() {
      isDrawing = false;
      ctx.beginPath();
    }

    function draw(e) {
      if (!isDrawing) return;
      
      const rect = signatureCanvas.getBoundingClientRect();
      const x = (e.clientX || e.touches[0].clientX) - rect.left;
      const y = (e.clientY || e.touches[0].clientY) - rect.top;

      ctx.lineTo(x, y);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(x, y);
      hasSigned = true;
    }

    signatureCanvas.addEventListener('mousedown', startPosition);
    signatureCanvas.addEventListener('mouseup', endPosition);
    signatureCanvas.addEventListener('mousemove', draw);
    
    signatureCanvas.addEventListener('touchstart', (e) => { e.preventDefault(); startPosition(e); });
    signatureCanvas.addEventListener('touchend', endPosition);
    signatureCanvas.addEventListener('touchmove', (e) => { e.preventDefault(); draw(e); });

    btnClearSignature.addEventListener('click', (e) => {
      e.preventDefault();
      ctx.clearRect(0, 0, signatureCanvas.width, signatureCanvas.height);
      hasSigned = false;
    });

    btnCancelSignature.addEventListener('click', (e) => {
      e.preventDefault();
      signatureModal.style.display = 'none';
    });
    
    btnSaveSignature.addEventListener('click', (e) => {
      e.preventDefault();
      if (!hasSigned) {
        const errorEl = document.getElementById('signature_error');
        if (errorEl) errorEl.style.display = 'block';
        return;
      }
      signatureData = signatureCanvas.toDataURL('image/png');
      signatureModal.style.display = 'none';
      submitData(); // proceed to submit
    });
  }

  admissionForm.addEventListener('submit', function(e) {
    e.preventDefault();
    
    errorBanner.style.display = 'none';
    errorBanner.innerHTML = '';

    // Validate that all 5 consents are checked
    const consentCheckboxes = document.querySelectorAll('input[name="consents"]');
    let allChecked = true;
    consentCheckboxes.forEach(cb => {
      if (!cb.checked) {
        allChecked = false;
      }
    });

    if (!allChecked) {
      errorBanner.innerHTML = '<strong>Please complete all required Signed Consents before confirming admission.</strong>';
      errorBanner.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    const verificationMethod = document.querySelector('input[name="verification_method"]:checked').value;
    
    if (verificationMethod === 'upload') {
      const fileInput = document.getElementById('consent_file');
      if (!fileInput.files.length) {
        errorBanner.innerHTML = '<strong>Please select a scanned document to upload.</strong>';
        errorBanner.style.display = 'block';
        return;
      }
      submitData();
    } else {
      // e-Signature popup
      signatureModal.style.display = 'block';
    }
  });
  
  function submitData() {
    const originalBtnText = btnConfirmAdmission.innerHTML;
    btnConfirmAdmission.innerHTML = 'Saving...';
    btnConfirmAdmission.disabled = true;

    const residentId = document.getElementById('resident_id').value;
    const admissionDate = document.getElementById('admission_date').value;
    const bedId = document.getElementById('room_assignment').value;
    const verificationMethod = document.querySelector('input[name="verification_method"]:checked').value;
    
    // Care Team and Payer
    const payerSource = document.getElementById('payer_source').value;
    const payerName = document.getElementById('payer_name').value;
    const physician = document.getElementById('physician').value;
    const physicianNpi = document.getElementById('physician_npi').value;
    const nurse = document.getElementById('nurse').value;
    const orderDate = document.getElementById('order_date').value;
    
    const formData = new FormData();
    formData.append('resident', residentId);
    formData.append('admission_date', admissionDate);
    formData.append('bed_id', bedId);
    
    // Facility is required by model, send a default ID 1
    formData.append('facility', 1);
    
    formData.append('verification_method', verificationMethod);
    
    // Append new fields
    if (payerSource) formData.append('payer_source', payerSource);
    if (payerName) formData.append('payer_name', payerName);
    if (physician) formData.append('physician_name', physician);
    if (physicianNpi) formData.append('physician_npi', physicianNpi);
    if (nurse) formData.append('nurse_name', nurse);
    if (orderDate) formData.append('order_date', orderDate);
    
    if (verificationMethod === 'upload') {
      const fileInput = document.getElementById('consent_file');
      formData.append('consent_file', fileInput.files[0]);
    } else if (verificationMethod === 'esignature' && signatureData) {
      formData.append('consent_signature', signatureData);
    }

    const csrfElement = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfToken = csrfElement ? csrfElement.value : '';

    fetch('/api/v1/medical/admissions/create/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': csrfToken
      },
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      window.location.href = `/medical/initial-assessment/${residentId}/`;
    })
    .catch(error => {
      console.error('Error:', error);
      btnConfirmAdmission.innerHTML = originalBtnText;
      btnConfirmAdmission.disabled = false;
      errorBanner.innerHTML = '<strong>Error saving admission data. Please try again.</strong>';
      errorBanner.style.display = 'block';
    });
  }
});
