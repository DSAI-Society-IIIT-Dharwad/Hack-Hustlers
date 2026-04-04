/* ═══════════════════════════════════════════════════════════════
   consultation.js — Real-time voice consultation
   ═══════════════════════════════════════════════════════════════ */

let consultationId = null;
let currentDoctor = null;
let isRecording = false;
let recordingStartTime = null;
let mediaRecorder = null;
let audioChunks = [];
let durationInterval = null;
let currentLanguage = 'en';

document.addEventListener('DOMContentLoaded', async () => {
  // Get consultation ID from URL
  const params = new URLSearchParams(window.location.search);
  consultationId = params.get('consultation_id');

  if (!consultationId) {
    alert('No consultation ID provided');
    window.location.href = '/patient';
    return;
  }

  // Load consultation details
  await loadConsultationDetails();
  startDurationCounter();
  
  // Setup language selector
  document.querySelectorAll('.lang-option').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.lang-option').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentLanguage = e.target.dataset.lang;
    });
  });
});

async function loadConsultationDetails() {
  try {
    // Simulate loading consultation details
    document.getElementById('doctorNameHeader').textContent = 'Dr. Priya Sharma';
    document.getElementById('doctorSpecHeader').textContent = 'Cardiologist · NMC Verified';
  } catch (err) {
    console.error('Error loading consultation:', err);
  }
}

function startDurationCounter() {
  let seconds = 0;
  durationInterval = setInterval(() => {
    seconds++;
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    const timeStr = [hours, minutes, secs]
      .map(x => String(x).padStart(2, '0'))
      .join(':');
    document.getElementById('durationTime').textContent = timeStr;
  }, 1000);
}

async function toggleRecording() {
  if (!isRecording) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];
      
      mediaRecorder.ondataavailable = (e) => {
        audioChunks.push(e.data);
      };
      
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        await processAudio(audioBlob);
      };
      
      mediaRecorder.start();
      isRecording = true;
      document.getElementById('recordBtn').textContent = '⏹ Stop';
      document.getElementById('recordBtn').style.background = '#ef4444';
      document.getElementById('asrModal').style.display = 'flex';
      recordingStartTime = Date.now();
      
      // Update recording time
      let recordingTime = 0;
      const recordingInterval = setInterval(() => {
        recordingTime++;
        const mins = Math.floor(recordingTime / 60);
        const secs = recordingTime % 60;
        document.getElementById('recordingTime').textContent =
          `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
        
        if (!isRecording) clearInterval(recordingInterval);
      }, 1000);
    } catch (err) {
      alert('Microphone access denied');
    }
  } else {
    stopRecording();
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
    isRecording = false;
    document.getElementById('recordBtn').textContent = '🎙️ Record';
    document.getElementById('recordBtn').style.background = 'rgba(0, 212, 255, 0.2)';
    setTimeout(() => {
      document.getElementById('asrModal').style.display = 'none';
    }, 1000);
  }
}

async function processAudio(audioBlob) {
  try {
    document.getElementById('asrStatus').textContent = '🔄 Processing speech...';
    
    // Simulate ASR (Automatic Speech Recognition)
    // In production, send to real ASR API (Google Speech-to-Text, Azure, etc.)
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('language', currentLanguage);
    
    // Simulate ASR response
    const recognizedText = 'I have been experiencing chest pain for the past 3 days';
    
    // Add to chat
    addMessageToChat('patient', recognizedText);
    
    // Clear input
    document.getElementById('messageInput').value = '';
    
    // Simulate doctor response
    setTimeout(() => {
      addMessageToChat('doctor', 'I understand. Let me ask you some follow-up questions.');
    }, 1000);
    
  } catch (err) {
    console.error('Error processing audio:', err);
    document.getElementById('asrStatus').textContent = 'Error processing audio';
  }
}

function addMessageToChat(sender, text) {
  const messagesDiv = document.getElementById('consultationMessages');
  const messageEl = document.createElement('div');
  messageEl.className = `message ${sender}`;
  messageEl.innerHTML = `
    <div class="message-balloon">
      ${text}
    </div>
  `;
  messagesDiv.appendChild(messageEl);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function sendMessage() {
  const text = document.getElementById('messageInput').value.trim();
  if (!text) return;
  
  addMessageToChat('patient', text);
  document.getElementById('messageInput').value = '';
  
  // Simulate doctor response
  setTimeout(() => {
    addMessageToChat('doctor', 'Thank you for providing that information. Let me analyze your symptoms and suggest some tests.');
  }, 1000);
}

function switchTab(tabName) {
  // Hide all tabs
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  
  // Show selected tab
  document.getElementById(tabName + 'Tab').classList.add('active');
  
  // Update tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  event.target.classList.add('active');
}

function addSymptom() {
  const symptomInput = document.getElementById('symptomInput');
  const symptomText = symptomInput.value.trim();
  
  if (!symptomText) return;
  
  const symptomsList = document.getElementById('symptomsList');
  const symptomEl = document.createElement('div');
  symptomEl.className = 'symptom-item';
  symptomEl.innerHTML = `
    <span class="symptom-name">${symptomText}</span>
    <span class="symptom-duration">Duration: Just added</span>
  `;
  symptomsList.appendChild(symptomEl);
  
  symptomInput.value = '';
}

function endConsultation() {
  if (confirm('Are you sure you want to end the consultation?')) {
    if (durationInterval) clearInterval(durationInterval);
    // In production, call API to close consultation
    setTimeout(() => {
      window.location.href = '/ai-analysis.html?consultation=' + consultationId;
    }, 500);
  }
}
