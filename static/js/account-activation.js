document.addEventListener('DOMContentLoaded', async () => {
    const activationForm = document.getElementById('activationForm');
    const loadingState = document.getElementById('loadingState');
    const globalError = document.getElementById('globalError');
    const successState = document.getElementById('successState');
    const submitBtn = document.getElementById('submitBtn');

    if (!activationForm) return;

    const apiUrl = activationForm.getAttribute('data-api-url');
    const redirectUrl = activationForm.getAttribute('data-redirect-url');

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

    function clearErrors() {
        globalError.style.display = 'none';
        globalError.textContent = '';

        const errorFields = ['passwordError', 'confirmPasswordError', 'phoneError', 'termsError'];
        errorFields.forEach(id => {
            const el = document.getElementById(id);
            if (el) {
                el.style.display = 'none';
                el.textContent = '';
            }
        });
    }

    function displayError(fieldId, message) {
        const el = document.getElementById(fieldId);
        if (el) {
            el.textContent = message;
            el.style.display = 'block';
        }
    }

    // Initial GET request to validate token and populate form
    try {
        const response = await fetch(apiUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
            }
        });

        let data;
        try {
            data = await response.json();
        } catch (err) {
            throw new Error('Invalid server response format.');
        }

        if (!response.ok) {
            throw new Error(data.detail || 'Activation link is invalid or expired.');
        }

        // Success: populate fields
        document.getElementById('email').value = data.email || '';
        document.getElementById('phone_number').value = data.phone_number || '';

        loadingState.style.display = 'none';
        activationForm.style.display = 'block';

    } catch (error) {
        loadingState.style.display = 'none';
        globalError.textContent = error.message;
        globalError.style.display = 'block';
        return; // Stop initialization
    }

    // Form submission
    activationForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        clearErrors();

        const password = document.getElementById('password').value; // Untrimmed
        const confirm_password = document.getElementById('confirm_password').value; // Untrimmed
        const phone_number = document.getElementById('phone_number').value; // Untrimmed
        const accept_terms = document.getElementById('accept_terms').checked;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Activating...';

        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({
                    password,
                    confirm_password,
                    phone_number,
                    accept_terms
                })
            });

            let data;
            try {
                data = await response.json();
            } catch (err) {
                throw new Error('Invalid server response format.');
            }

            if (!response.ok) {
                if (data.detail) {
                    throw new Error(data.detail);
                }

                // Handle field-specific validation errors
                let fieldErrors = false;
                if (data.password && data.password.length > 0) {
                    displayError('passwordError', data.password[0]);
                    fieldErrors = true;
                }
                if (data.confirm_password && data.confirm_password.length > 0) {
                    displayError('confirmPasswordError', data.confirm_password[0]);
                    fieldErrors = true;
                }
                if (data.phone_number && data.phone_number.length > 0) {
                    displayError('phoneError', data.phone_number[0]);
                    fieldErrors = true;
                }
                if (data.accept_terms && data.accept_terms.length > 0) {
                    displayError('termsError', data.accept_terms[0]);
                    fieldErrors = true;
                }

                if (!fieldErrors) {
                    throw new Error('An unexpected validation error occurred.');
                }
            } else {
                // Success
                activationForm.style.display = 'none';
                successState.style.display = 'block';

                setTimeout(() => {
                    window.location.href = redirectUrl;
                }, 2000); // Redirect after 2s delay
            }

        } catch (error) {
            globalError.textContent = error.message || 'Network error. Please try again.';
            globalError.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Activate account';
        }
    });
});
