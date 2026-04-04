/* ═══════════════════════════════════════════════════════════════
   medical-report.js — Medical Report Generation & PDF Export
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {
  // Load report data
  await loadReportData();
  
  // Setup language selector
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      changeReportLanguage(e.target.dataset.lang);
    });
  });
});

async function loadReportData() {
  try {
    // Get report ID from URL
    const params = new URLSearchParams(window.location.search);
    const reportId = params.get('report_id') || 'MR-2024-001';
    
    // Load patient data
    const user = Auth.getUser();
    document.getElementById('reportPatientName').textContent = user?.name || 'Patient Name';
    document.getElementById('reportPatientAge').textContent = user?.age || '25';
    document.getElementById('reportBloodGroup').textContent = user?.blood_group || 'O+';
    document.getElementById('reportContact').textContent = user?.email || 'patient@email.com';
    document.getElementById('reportDate').textContent = new Date().toLocaleDateString('en-IN');
    
    // Load doctor data
    document.getElementById('reportDoctorName').textContent = 'Dr. Priya Sharma';
    document.getElementById('reportSpecialization').textContent = 'Cardiologist';
    document.getElementById('reportNmcId').textContent = 'NMC20034521';
    document.getElementById('reportExperience').textContent = '12 years';
    
  } catch (err) {
    console.error('Error loading report:', err);
  }
}

function changeReportLanguage(lang) {
  console.log('Changing report language to:', lang);
  // In production, this would load translated version from backend
  // For now, just update the visual indication
  if (lang === 'hi') {
    alert('हिंदी में रिपोर्ट लोड हो रही है...');
  } else if (lang === 'kn') {
    alert('ಕನ್ನಡದಲ್ಲಿ ವರದಿ ಲೋಡ್ ಆಗುತ್ತಿದೆ...');
  }
}

function downloadReport() {
  try {
    const element = document.querySelector('.report-content');
    const opt = {
      margin: 10,
      filename: 'medical-report.pdf',
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm', format: 'a4' }
    };
    
    // Using html2pdf library
    html2pdf().set(opt).from(element).save();
  } catch (err) {
    console.error('Error downloading report:', err);
    alert('Error generating PDF. Please try again.');
  }
}

function shareReport() {
  const reportLink = window.location.href;
  
  if (navigator.share) {
    navigator.share({
      title: 'Medical Consultation Report',
      text: 'View my medical consultation report',
      url: reportLink
    });
  } else {
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(reportLink);
    alert('Report link copied to clipboard!');
  }
}

function goToFeedback() {
  window.location.href = '/feedback.html';
}

// Print functionality
document.addEventListener('keydown', (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
    e.preventDefault();
    window.print();
  }
});
