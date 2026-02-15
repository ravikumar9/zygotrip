/**
 * Booking Timer
 * Countdown timer for booking expiration (10 minutes)
 * Cancels booking if timer expires
 */

class BookingTimer {
  constructor(expiresAtISO, bookingId) {
    this.expiresAt = new Date(expiresAtISO);
    this.bookingId = bookingId;
    this.timerElement = document.querySelector('[data-booking-timer]');
    this.minutesElement = document.querySelector('[data-timer-minutes]');
    this.secondsElement = document.querySelector('[data-timer-seconds]');
    this.warningElement = document.querySelector('[data-timer-warning]');
    
    if (!this.timerElement) return;
    
    this.startTimer();
  }

  startTimer() {
    this.updateDisplay();
    
    // Update every second
    this.interval = setInterval(() => {
      if (this.updateDisplay()) {
        // Timer expired
        this.onExpired();
      }
    }, 1000);
  }

  updateDisplay() {
    const now = new Date();
    const remaining = this.expiresAt - now;
    
    if (remaining <= 0) {
      // Timer expired
      if (this.minutesElement) this.minutesElement.textContent = '0';
      if (this.secondsElement) this.secondsElement.textContent = '00';
      if (this.warningElement) this.warningElement.classList.add('is-critical');
      clearInterval(this.interval);
      return true;
    }

    const totalSeconds = Math.floor(remaining / 1000);
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;

    if (this.minutesElement) this.minutesElement.textContent = minutes;
    if (this.secondsElement) this.secondsElement.textContent = String(seconds).padStart(2, '0');

    // Show warning if less than 2 minutes
    if (minutes < 2 && this.warningElement) {
      this.warningElement.classList.add('is-warning');
    }

    return false;
  }

  onExpired() {
    alert('⏰ Your booking session has expired. Please start a new booking.');
    
    // Cancel the booking and redirect
    const bookingUuid = this.bookingId;
    fetch(`/booking/${bookingUuid}/cancel/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || '',
      },
    })
    .then(() => {
      window.location.href = '/hotels/';
    })
    .catch(() => {
      window.location.href = '/hotels/';
    });
  }

  stop() {
    if (this.interval) clearInterval(this.interval);
  }
}

// Initialize timer when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const timerElement = document.querySelector('[data-booking-timer]');
  if (timerElement) {
    const expiresAt = timerElement.getAttribute('data-expires-at');
    const bookingId = timerElement.getAttribute('data-booking-id');
    if (expiresAt) {
      new BookingTimer(expiresAt, bookingId);
    }
  }
});
