/* ═══════════════════════════════════════════════════════════════
   ai-analysis.js — AI Diagnosis & Analysis
   ═══════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', async () => {
  await loadAnalysisData();
});

async function loadAnalysisData() {
  try {
    // Simulate loading consultation data
    populateSymptoms();
    populateDiagnosis();
    populateRecommendations();
    populatePrescriptions();
  } catch (err) {
    console.error('Error loading analysis:', err);
  }
}

function populateSymptoms() {
  const symptoms = [
    { name: 'Chest Pain', duration: '3 days' },
    { name: 'Shortness of Breath', duration: '2 days' },
    { name: 'Mild Dizziness', duration: '1 day' }
  ];
  
  const symptomsList = document.getElementById('symptomsList');
  symptomsList.innerHTML = symptoms.map(s => `
    <div class="symptom-item">
      <span class="symptom-name">${s.name}</span>
      <span class="symptom-duration">Duration: ${s.duration}</span>
    </div>
  `).join('');
}

function populateDiagnosis() {
  const diagnosisBox = document.getElementById('diagnosisBox');
  diagnosisBox.innerHTML = `
    <div style="padding: 20px; background: rgba(16, 185, 129, 0.05); border-radius: 8px;">
      <h3 style="margin-bottom: 15px; color: #10b981;">Based on AI analysis of reported symptoms:</h3>
      <p style="line-height: 1.8; color: #f0f6ff; font-size: 14px;">
        The symptom cluster suggests possible <strong>Stable Angina Pectoris</strong> with associated anxiety. 
        Chest pain combined with shortness of breath and dizziness warrants immediate cardiac evaluation. 
        However, differential diagnoses may include gastroesophageal reflux disease (GERD), musculoskeletal chest pain, 
        or panic disorder. Recommend ECG, troponin levels, and cardiology consultation for definitive diagnosis.
      </p>
    </div>
  `;
}

function populateRecommendations() {
  const recommendations = [
    'Low sodium diet, avoid caffeine and heavy foods',
    'Light walking for 20 minutes daily',
    'Maintain 7-8 hours of sleep',
    'Practice meditation and yoga',
    'Limit alcohol to 1 unit per day'
  ];
  
  const list = document.getElementById('lifestyleRecommendations');
  list.innerHTML = recommendations.map(r => `
    <div class="recommendation">
      <strong>${r.split(':')[0]}:</strong> ${r.split(':')[1] || r}
    </div>
  `).join('');
}

function populatePrescriptions() {
  const medicines = [
    { name: 'Aspirin', dosage: '100 mg', frequency: 'Once daily', duration: '7 days', instructions: 'Take with food' },
    { name: 'Amlodipine', dosage: '5 mg', frequency: 'Once daily', duration: 'Ongoing', instructions: 'Take with or without food' },
    { name: 'Metformin', dosage: '500 mg', frequency: 'Twice daily', duration: 'Ongoing', instructions: 'Take with meals' }
  ];
  
  const tbody = document.getElementById('medicineList');
  tbody.innerHTML = medicines.map(m => `
    <tr>
      <td>${m.name}</td>
      <td>${m.dosage}</td>
      <td>${m.frequency}</td>
      <td>${m.duration}</td>
      <td>${m.instructions}</td>
    </tr>
  `).join('');
}

function goToReport() {
  window.location.href = '/medical-report.html';
}
