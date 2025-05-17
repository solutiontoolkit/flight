
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.cancel-btn').forEach(function(button) {
            button.addEventListener('click', function() {
                const bookingId = this.getAttribute('data-booking-id');
                if (confirm('Are you sure you want to cancel this booking?')) {
                    fetch(`/cancel_booking/${bookingId}`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Remove row
                            const row = this.closest('tr');
                            row.remove();
                            alert(data.success);
                        } else if (data.error) {
                            alert(data.error);
                        }
                    })
                    .catch(error => {
                        alert('An error occurred. Please try again.');
                    });
                }
            });
        });
    });
