document.addEventListener('DOMContentLoaded', () => {
    if (!('webkitSpeechRecognition' in window)) {
        console.log('Speech Recognition not supported in this browser.');
        return;
    }

    const recognition = new window.webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    let currentInput = null;
    let inactivityTimer = null;

    const voicePopup = document.createElement('div');
    voicePopup.id = 'voice-popup';
    voicePopup.style.cssText = `
        display:none;
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%);
        background: #222; color: white;
        padding: 20px 30px;
        border-radius: 10px;
        box-shadow: 0 0 15px rgba(0,0,0,0.6);
        text-align: center;
        z-index: 1000;
        font-family: Arial, sans-serif;
    `;

    voicePopup.innerHTML = `
        <div id="mic-icon" style="font-size: 48px; margin-bottom: 10px; color: #ff3b30;">🎤</div>
        <div id="voice-msg" style="font-size: 18px;">Speak now...</div>
        <button id="voice-cancel-btn" style="
            margin-top: 15px;
            background: #ff3b30;
            border: none;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        ">Cancel</button>
    `;

    document.body.appendChild(voicePopup);

    const cancelBtn = voicePopup.querySelector('#voice-cancel-btn');
    const voiceMsg = voicePopup.querySelector('#voice-msg');

    function startRecognition(input) {
        currentInput = input;
        voicePopup.style.display = 'block';
        voiceMsg.textContent = 'Speak now...';
        recognition.start();
    }

    function stopRecognition() {
        recognition.stop();
        voicePopup.style.display = 'none';
        currentInput = null;
    }

    recognition.onresult = (event) => {
        if (currentInput) {
            let transcript = event.results[0][0].transcript.trim();
            transcript = transcript.replace(/[.,!?]$/, '');

            if (currentInput.tagName === 'SELECT') {
                const options = Array.from(currentInput.options);
                const match = options.find(opt =>
                    opt.text.toLowerCase().includes(transcript.toLowerCase())
                );
                if (match) {
                    currentInput.value = match.value;
                } else {
                    alert('No matching option found: ' + transcript);
                }
            } else {
                currentInput.value = transcript;
            }

            stopRecognition();
        }
    };

    recognition.onerror = (event) => {
        alert('Speech recognition error: ' + event.error);
        stopRecognition();
    };

    recognition.onend = () => {
        if (voicePopup.style.display === 'block') {
            stopRecognition();
        }
    };

    cancelBtn.addEventListener('click', stopRecognition);

    const inputs = document.querySelectorAll(
        '.sign-in-container input, .sign-up-container input, ' +
        '.trip-form input[type="text"], .trip-form input[type="date"], .trip-form select, ' +
        '.form-container input, .form-container select'
      );
      console.log("Voice input targets:", inputs);
      
      
    
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            clearTimeout(inactivityTimer);
            inactivityTimer = setTimeout(() => {
                if (!input.value.trim()) {
                    startRecognition(input);
                }
            }, 7000); // 7 seconds
        });

        input.addEventListener('input', () => {
            clearTimeout(inactivityTimer);
        });

        input.addEventListener('blur', () => {
            clearTimeout(inactivityTimer);
        });
    });

    window.addEventListener('click', (e) => {
        if (
            voicePopup.style.display === 'block' &&
            !voicePopup.contains(e.target) &&
            !e.target.matches('input, select')
        ) {
            stopRecognition();
        }
    });
});


  document.addEventListener("DOMContentLoaded", function () {
    const message = document.getElementById("welcome-message");
    const closeBtn = document.getElementById("close-btn");

    // Dismiss after 7 seconds
    setTimeout(() => {
      if (message) message.style.display = "none";
    }, 7000);

    // Manual close
    if (closeBtn) {
      closeBtn.addEventListener("click", () => {
        message.style.display = "none";
      });
    }
  });



  
  document.addEventListener("DOMContentLoaded", () => {
    const voiceBtn = document.getElementById("voice-book-logo");
  
    if (!('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
      alert("Your browser does not support Speech Recognition. Try Chrome.");
      return;
    }
  
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';
    recognition.interimResults = false;
  
    const questions = [
      { field: "from_location", prompt: "Where are you flying from?" },
      { field: "to_location", prompt: "Where are you flying to?" },
      { field: "depart_date", prompt: "What is your departure date?" },
      { field: "return_date", prompt: "What is your return date?" },
      { field: "flight_time", prompt: "What time do you want to fly?" },
      { field: "adults", prompt: "How many adults are flying?" },
      { field: "children", prompt: "How many children?" },
      { field: "infants", prompt: "How many infants?" },
      { field: "class_of_travel", prompt: "What class do you want to travel in? Economy, Business, or First class?" },
      { field: "airline_name", prompt: "Do you have a preferred airline?" }
    ];
  
    let current = 0;
  
    voiceBtn.addEventListener("click", () => {
      current = 0;
      askNextQuestion();
    });
  
    function askNextQuestion() {
      if (current >= questions.length) {
        speak("Thank you. Your booking details have been filled.");
        return;
      }
  
      const q = questions[current];
      speak(q.prompt);
      recognition.start();
    }
  
    recognition.onresult = function (event) {
      const transcript = event.results[0][0].transcript;
      const fieldId = questions[current].field;
      const input = document.getElementsByName(fieldId)[0];
  
      if (input) {
        if (input.tagName === "SELECT") {
          for (let option of input.options) {
            if (option.text.toLowerCase().includes(transcript.toLowerCase())) {
              input.value = option.value;
              break;
            }
          }
        } else {
          if (fieldId.includes("date")) {
            input.value = parseDate(transcript);
          } else if (fieldId.includes("time")) {
            input.value = parseTime(transcript);
          } else {
            input.value = transcript;
          }
        }
      }
  
      current++;
      setTimeout(askNextQuestion, 800);
    };
  
    recognition.onerror = function () {
      speak("Sorry, I didn't catch that. Let's try again.");
      askNextQuestion();
    };
  
    function speak(text) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'en-US';
      speechSynthesis.speak(utterance);
    }
  
    function parseDate(spokenDate) {
      const date = new Date(spokenDate);
      if (!isNaN(date)) {
        return date.toISOString().split("T")[0]; // yyyy-mm-dd
      }
      return "";
    }
  
    function parseTime(spokenTime) {
      try {
        let parts = spokenTime.match(/(\d+)(?::(\d+))?\s*(AM|PM)?/i);
        if (!parts) return "";
        let hour = parseInt(parts[1]);
        let minutes = parts[2] ? parseInt(parts[2]) : 0;
        let meridian = parts[3];
  
        if (meridian && meridian.toLowerCase() === "pm" && hour < 12) hour += 12;
        if (meridian && meridian.toLowerCase() === "am" && hour === 12) hour = 0;
  
        return `${hour.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
      } catch (err) {
        return "";
      }
    }
  });
  

  document.addEventListener("DOMContentLoaded", () => {
    const bookingBtn = document.getElementById("proceed-booking-btn");
  
    bookingBtn.addEventListener("click", (e) => {
      e.preventDefault(); // prevent default anchor behavior
  
      fetch("/check_session")
        .then(res => res.json())
        .then(data => {
          if (data.logged_in) {
            window.location.href = "/booking";
          } else {
            alert("Please sign in to book a flight."); // optional
            window.location.href = "/account";
          }
        });
    });
  });