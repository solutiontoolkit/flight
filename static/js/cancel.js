document.querySelectorAll('.cancel-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const bookingId = btn.getAttribute('data-booking-id');
      if (!confirm('Are you sure you want to cancel this booking?')) return;
  
      fetch(`/cancel_booking/${bookingId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrf_token')  // if you have CSRF protection
        }
      }).then(response => {
        if (response.redirected) {
          window.location.href = response.url;
        } else {
          // optionally reload or update UI after cancellation
          window.location.reload();
        }
      }).catch(error => {
        alert('Error cancelling booking: ' + error);
      });
    });
  });
  
  // Helper to get cookie for CSRF token if needed (Flask-WTF)
  function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        cookie = cookie.trim();
        if (cookie.startsWith(name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }
  