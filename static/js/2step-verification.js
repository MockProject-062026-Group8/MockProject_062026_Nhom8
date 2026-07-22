document.addEventListener('DOMContentLoaded', () => {
    const otpForm = document.getElementById('otpForm');
    const displayPhone = document.getElementById('displayPhone');
    const otpInputs = Array.from(document.querySelectorAll('.otp-input'));
    const verifyBtn = document.getElementById('verifyBtn');
    const resendBtn = document.getElementById('resendBtn');
    const resendTimer = document.getElementById('resendTimer');
    const globalError = document.getElementById('globalError');
    const globalSuccess = document.getElementById('globalSuccess');
    const otpFieldError = document.getElementById('otpFieldError');
    const differentAccountLink = document.getElementById('differentAccountLink');

    if (!otpForm) return;

    const verifyUrl = otpForm.getAttribute('data-verify-url');
    const resendUrl = otpForm.getAttribute('data-resend-url');
    const loginUrl = otpForm.getAttribute('data-login-url');

    let token = sessionStorage.getItem('verification_token');
    let maskedPhone = sessionStorage.getItem('masked_phone_number');

    if (!token) {
        window.location.href = loginUrl;
        return;
    }

    displayPhone.textContent = maskedPhone || '';

    // OTP Input Logic
    otpInputs.forEach((input, index) => {
        input.addEventListener('input', (e) => {
            const val = e.target.value;
            if (!/^\d$/.test(val)) {
                e.target.value = '';
                return;
            }
            if (index < otpInputs.length - 1 && val !== '') {
                otpInputs[index + 1].focus();
            }
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Backspace' && e.target.value === '' && index > 0) {
                otpInputs[index - 1].focus();
            }
        });

        input.addEventListener('paste', (e) => {
            e.preventDefault();
            const pasteData = (e.clipboardData || window.clipboardData).getData('text');
            const digits = pasteData.replace(/\D/g, '').split('').slice(0, 6);
            digits.forEach((digit, i) => {
                if (i < otpInputs.length) {
                    otpInputs[i].value = digit;
                    if (i < otpInputs.length - 1) {
                        otpInputs[i + 1].focus();
                    } else {
                        otpInputs[i].focus();
                    }
                }
            });
        });
    });

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

    // Verify
    otpForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        globalError.style.display = 'none';
        globalError.textContent = '';
        otpFieldError.style.display = 'none';
        otpFieldError.textContent = '';
        globalSuccess.style.display = 'none';

        const otpCode = otpInputs.map(i => i.value).join('');
        if (otpCode.length !== 6) {
            otpFieldError.textContent = 'Please enter a 6-digit code.';
            otpFieldError.style.display = 'block';
            return;
        }

        verifyBtn.disabled = true;
        verifyBtn.textContent = 'Verifying...';

        try {
            const response = await fetch(verifyUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({
                    verification_token: token,
                    otp_code: otpCode
                })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                if (data.otp_code) {
                    otpFieldError.textContent = Array.isArray(data.otp_code) ? data.otp_code[0] : data.otp_code;
                    otpFieldError.style.display = 'block';
                    otpInputs.forEach(i => i.value = '');
                    otpInputs[0].focus();
                } else if (data.detail) {
                    globalError.textContent = data.detail;
                    globalError.style.display = 'block';
                    otpInputs.forEach(i => i.value = '');
                    otpInputs[0].focus();
                } else {
                    globalError.textContent = 'Verification failed. Please try again.';
                    globalError.style.display = 'block';
                }
                return;
            }

            if (data.access && data.refresh) {
                sessionStorage.setItem('access_token', data.access);
                sessionStorage.setItem('refresh_token', data.refresh);
                sessionStorage.removeItem('verification_token');
                sessionStorage.removeItem('masked_phone_number');

                otpForm.style.display = 'none';
                globalSuccess.textContent = 'Verification successful.';
                globalSuccess.style.display = 'block';
            } else {
                throw new Error('Invalid server response: missing tokens.');
            }

        } catch (error) {
            globalError.textContent = error.message || 'Network error. Please try again.';
            globalError.style.display = 'block';
        } finally {
            verifyBtn.disabled = false;
            verifyBtn.textContent = 'Verify';
        }
    });

    // Countdown Timer
    let countdownInterval;
    function startCountdown(seconds) {
        clearInterval(countdownInterval);

        function updateTimer() {
            if (seconds <= 0) {
                clearInterval(countdownInterval);
                resendTimer.textContent = '';
                return;
            }
            const m = Math.floor(seconds / 60).toString().padStart(2, '0');
            const s = (seconds % 60).toString().padStart(2, '0');
            resendTimer.textContent = `(${m}:${s})`;
            seconds--;
        }

        updateTimer();
        countdownInterval = setInterval(updateTimer, 1000);
    }

    startCountdown(300);

    // Resend
    resendBtn.addEventListener('click', async () => {
        if (resendBtn.disabled) return;

        globalError.style.display = 'none';
        globalError.textContent = '';
        otpFieldError.style.display = 'none';
        otpFieldError.textContent = '';
        globalSuccess.style.display = 'none';

        resendBtn.disabled = true;

        try {
            const response = await fetch(resendUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken') || ''
                },
                body: JSON.stringify({
                    verification_token: token
                })
            });

            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                globalError.textContent = data.detail || 'Resend failed. Please try again.';
                globalError.style.display = 'block';
                resendBtn.disabled = false;
                return;
            }

            if (data.verification_token) {
                token = data.verification_token;
                sessionStorage.setItem('verification_token', token);

                if (data.phone_number) {
                    maskedPhone = data.phone_number;
                    sessionStorage.setItem('masked_phone_number', maskedPhone);
                    displayPhone.textContent = maskedPhone;
                }

                otpInputs.forEach(i => i.value = '');
                otpInputs[0].focus();

                startCountdown(data.expires_in || 300);
            }

        } catch (error) {
            globalError.textContent = 'Network error. Please try again.';
            globalError.style.display = 'block';
            resendBtn.disabled = false;
        }
    });

    // Use a different account
    if (differentAccountLink) {
        differentAccountLink.addEventListener('click', (e) => {
            e.preventDefault();
            sessionStorage.removeItem('verification_token');
            sessionStorage.removeItem('masked_phone_number');
            sessionStorage.removeItem('access_token');
            sessionStorage.removeItem('refresh_token');
            window.location.href = loginUrl;
        });
    }
});
