/* ═══════════════════════════════════════════════════════════════
   feedback.js — Feedback & Rating System
   ═══════════════════════════════════════════════════════════════ */

let ratings = {
  overall: 0,
  doctorQuality: 0,
  communication: 0,
  timeManagement: 0,
  easeOfUse: 0,
  technicalQuality: 0
};

document.addEventListener('DOMContentLoaded', () => {
  // Load doctor info
  loadDoctorInfo();
  
  // Setup star ratings
  setupStarRatings();
  
  // Setup form submission
  document.getElementById('feedbackForm').addEventListener('submit', handleSubmit);
  
  // Setup text area character counter
  const feedbackText = document.getElementById('feedbackText');
  feedbackText.addEventListener('input', () => {
    document.getElementById('charCount').textContent = feedbackText.value.length;
  });
});

function loadDoctorInfo() {
  // Get doctor info from URL or session
  const doctorName = 'Dr. Priya Sharma';
  const doctorSpec = 'Cardiologist';
  
  document.querySelectorAll('#doctorNameFeedback, #doctorNameRecommend').forEach(el => {
    el.textContent = doctorName;
  });
  document.getElementById('doctorSpecFeedback').textContent = `${doctorSpec} · NMC Verified`;
  document.getElementById('doctorAvatarFeedback').textContent = doctorName.split(' ').map(n => n[0]).join('');
}

function setupStarRatings() {
  const ratingGroups = [
    { id: 'overallRating', key: 'overall' },
    { id: 'doctorQualityRating', key: 'doctorQuality' },
    { id: 'communicationRating', key: 'communication' },
    { id: 'timeManagementRating', key: 'timeManagement' },
    { id: 'easeOfUseRating', key: 'easeOfUse' },
    { id: 'technicalQualityRating', key: 'technicalQuality' }
  ];
  
  ratingGroups.forEach(group => {
    const container = document.getElementById(group.id);
    const stars = container.querySelectorAll('.star');
    
    stars.forEach(star => {
      star.addEventListener('click', () => {
        const value = parseInt(star.dataset.value);
        ratings[group.key] = value;
        
        // Update visual state
        stars.forEach((s, index) => {
          if (index < value) {
            s.classList.add('active');
          } else {
            s.classList.remove('active');
          }
        });
      });
      
      // Hover effect
      star.addEventListener('mouseenter', () => {
        const value = parseInt(star.dataset.value);
        stars.forEach((s, index) => {
          if (index < value) {
            s.style.color = '#fbbf24';
            s.style.transform = 'scale(1.2)';
          }
        });
      });
    });
    
    container.addEventListener('mouseleave', () => {
      stars.forEach(s => {
        if (!s.classList.contains('active')) {
          s.style.color = 'rgba(0, 212, 255, 0.3)';
          s.style.transform = 'scale(1)';
        }
      });
    });
  });
}

function handleSubmit(e) {
  e.preventDefault();
  
  // Validate ratings
  const requiredRatings = ['overall', 'doctorQuality', 'communication', 'timeManagement'];
  const missingRatings = requiredRatings.filter(r => ratings[r] === 0);
  
  if (missingRatings.length > 0) {
    alert('Please rate all categories');
    return;
  }
  
  // Collect form data
  const formData = {
    doctor_rating: ratings.doctorQuality,
    communication_rating: ratings.communication,
    time_management_rating: ratings.timeManagement,
    overall_satisfaction: ratings.overall,
    platform_ease_of_use: ratings.easeOfUse,
    technical_quality: ratings.technicalQuality,
    feedback_text: document.getElementById('feedbackText').value,
    would_recommend: document.querySelector('input[name="would_recommend"]:checked')?.value === 'true',
    improvements: Array.from(document.querySelectorAll('input[name="improvements"]:checked')).map(el => el.value),
    improvements_text: document.getElementById('improvementSuggestions').value,
    anonymous: document.querySelector('input[name="anonymous"]:checked')?.value === 'true',
    submitted_at: new Date().toISOString()
  };
  
  // Show success message
  showSuccessMessage();
  
  // In production, send to backend
  console.log('Feedback Data:', formData);
  
  // Redirect after 2 seconds
  setTimeout(() => {
    goToDashboard();
  }, 2000);
}

function showSuccessMessage() {
  const form = document.getElementById('feedbackForm');
  const successMsg = document.getElementById('successMessage');
  
  form.style.display = 'none';
  successMsg.style.display = 'flex';
  successMsg.classList.add('show');
}

function goToDashboard() {
  const user = Auth.getUser();
  window.location.href = user?.role === 'doctor' ? '/doctor' : '/patient';
}

function goBack() {
  history.back();
}
