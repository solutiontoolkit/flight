// static/js/tooltip.js

document.addEventListener("DOMContentLoaded", function () {
    const tooltips = {
        newBookingBtn: "Click to book a new flight.",
        logoutBtn: "Click here to safely log out of your account.",
    };

    Object.entries(tooltips).forEach(([id, message]) => {
        const el = document.getElementById(id);
        if (el) {
            const tooltip = document.createElement("div");
            tooltip.className = "custom-tooltip";
            tooltip.innerText = message;
            document.body.appendChild(tooltip);

            el.addEventListener("mouseover", () => {
                const rect = el.getBoundingClientRect();
                tooltip.style.top = `${rect.top - 35}px`;
                tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
                tooltip.style.opacity = 1;
            });

            el.addEventListener("mouseout", () => {
                tooltip.style.opacity = 0;
            });
        }
    });
});





  const slides = document.querySelectorAll('.bg-slide');
  let current = 0;

  function showSlide(index) {
    slides.forEach((slide, i) => {
      slide.style.opacity = (i === index) ? '1' : '0';
    });
  }

  function nextSlide() {
    current = (current + 1) % slides.length;
    showSlide(current);
  }

  showSlide(current);
  setInterval(nextSlide, 6000); // Change every 6 seconds


  
  const voiceBtn = document.getElementById('voiceBtn');

  voiceBtn.addEventListener('click', () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Your browser does not support speech recognition.');
      return;
    }

    const recognition = new webkitSpeechRecognition();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.start();

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.toLowerCase();
      console.log('You said:', transcript);
      alert('Heard: ' + transcript);

      // Example simple parsing logic:
      // You can improve with NLP or regex to extract each field
      // Here is a naive example:

      let bookingData = {
        tripType: '', from: '', to: '', date: '', time: '', airline: '', classType: ''
      };

      if (transcript.includes('round trip')) bookingData.tripType = 'round trip';
      else if (transcript.includes('one way')) bookingData.tripType = 'one way';

      // Extract from/to city (naive approach)
      const fromMatch = transcript.match(/from ([a-z\s]+)/);
      if (fromMatch) bookingData.from = fromMatch[1].trim();

      const toMatch = transcript.match(/to ([a-z\s]+)/);
      if (toMatch) bookingData.to = toMatch[1].trim();

      // Extract date/time - simplistic
      const dateMatch = transcript.match(/on ([a-z0-9\s]+)/);
      if (dateMatch) bookingData.date = dateMatch[1].trim();

      const timeMatch = transcript.match(/at ([0-9\s:apm]+)/);
      if (timeMatch) bookingData.time = timeMatch[1].trim();

      // Extract airline
      const airlines = ['arik air', 'dana air', 'air peace', 'aska', 'max air'];
      for (const airline of airlines) {
        if (transcript.includes(airline)) {
          bookingData.airline = airline;
          break;
        }
      }

      // Extract class
      if (transcript.includes('business class')) bookingData.classType = 'Business';
      else if (transcript.includes('economy class')) bookingData.classType = 'Economy';

      // Save to localStorage
      localStorage.setItem('voiceBookingData', JSON.stringify(bookingData));

      alert('Booking data saved! Proceed to booking page.');
    };

    recognition.onerror = (event) => {
      alert('Error occurred in recognition: ' + event.error);
    };
  });


