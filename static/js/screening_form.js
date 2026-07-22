document.addEventListener('DOMContentLoaded', function() {
  const screeningForm = document.getElementById('screeningForm');
  const btnSubmitScreening = document.getElementById('btnSubmitScreening');
  const complianceSuccess = document.getElementById('complianceSuccess');
  const complianceWarningContainer = document.getElementById('complianceWarningContainer');
  const warningSubtext = document.getElementById('warningSubtext');
  const successText = document.getElementById('successText');
  const overrideReasonInput = document.getElementById('override_reason');
  const overrideError = document.getElementById('override_error');
  
  let isComplianceChecked = false;
  let isFlagged = false;

  // Initially hide both
  complianceSuccess.style.display = 'none';
  complianceWarningContainer.style.display = 'none';

  function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
  }
  const csrftoken = getCsrfToken();

  function getFormData() {
    const clinical_needs = Array.from(document.querySelectorAll('input[name="clinical_needs"]:checked')).map(cb => cb.value);
    return {
      resident: document.getElementById('resident_id').value,
      status: document.getElementById('status').value,
      acuity_level: document.getElementById('acuity_level').value,
      estimated_care_hours: document.getElementById('estimated_care_hours').value || null,
      clinical_needs: clinical_needs,
      special_requirements: document.getElementById('special_requirements').value,
      override_reason: overrideReasonInput.value
    };
  }

  // Run Compliance Check automatically
  async function runComplianceCheck() {
    const data = getFormData();
    
    try {
      const response = await fetch('/api/v1/medical/screenings/compliance-check/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      isComplianceChecked = true;
      isFlagged = result.is_flagged;

      if (isFlagged) {
        complianceSuccess.style.display = 'none';
        complianceWarningContainer.style.display = 'block';
        warningSubtext.textContent = result.message.split('—')[1]?.trim() || result.message;
      } else {
        complianceWarningContainer.style.display = 'none';
        complianceSuccess.style.display = 'flex';
        // Format success text with count of selected needs
        const numNeeds = data.clinical_needs.length;
        successText.innerHTML = `Facility capability check: ${numNeeds} / ${numNeeds} selected needs are supported (see AD-05 -> Clinical Capability)`;
      }
    } catch (error) {
      console.error("Error during compliance check", error);
    }
  }

  // Trigger check on change
  document.getElementById('acuity_level').addEventListener('change', runComplianceCheck);
  document.querySelectorAll('input[name="clinical_needs"]').forEach(cb => {
    cb.addEventListener('change', runComplianceCheck);
  });
  
  // Run an initial check on load if needed
  runComplianceCheck();

  // Submit Screening
  screeningForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const errorBanner = document.getElementById('errorBanner');
    errorBanner.style.display = 'none';
    errorBanner.innerHTML = '';

    if (!isComplianceChecked) {
      errorBanner.innerHTML = '<strong>Please wait for the compliance check to finish.</strong>';
      errorBanner.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    if (isFlagged && overrideReasonInput.value.length < 20) {
      overrideError.style.display = 'block';
      overrideError.textContent = 'Override reason must be at least 20 characters long.';
      return;
    } else {
      overrideError.style.display = 'none';
    }

    const data = getFormData();
    data.compliance_flagged = isFlagged;

    const originalBtnText = btnSubmitScreening.textContent;
    btnSubmitScreening.innerHTML = 'Saving...';
    btnSubmitScreening.disabled = true;

    try {
      const response = await fetch('/api/v1/medical/screenings/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrftoken
        },
        body: JSON.stringify(data)
      });
      
      const result = await response.json();
      
      if (response.ok) {
        // Redirect to Step 2 (Admission Form)
        window.location.href = `/medical/admission-form/${data.resident}/`;
      } else {
        console.error("Validation Errors:", result);
        let errorHtml = '<strong>Please correct the following errors:</strong><ul class="error-list">';
        for (const [key, val] of Object.entries(result)) {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          errorHtml += `<li><b>${formattedKey}</b>: ${val}</li>`;
        }
        errorHtml += '</ul>';
        errorBanner.innerHTML = errorHtml;
        errorBanner.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    } catch (error) {
      console.error("Submission Error", error);
      errorBanner.innerHTML = '<strong>An error occurred while saving. Please try again.</strong>';
      errorBanner.style.display = 'block';
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } finally {
      btnSubmitScreening.innerHTML = originalBtnText;
      btnSubmitScreening.disabled = false;
    }
  });
});
