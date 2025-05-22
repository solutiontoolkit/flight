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


