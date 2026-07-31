const symptomForm = document.getElementById('symptomForm');
const resultBox = document.getElementById('resultBox');
const reminderList = document.getElementById('reminderList');
const hospitalList = document.getElementById('hospitalList');

async function loadStaticContent() {
  const [remindersRes, hospitalsRes] = await Promise.all([
    fetch('/api/reminders'),
    fetch('/api/hospitals')
  ]);

  const reminders = (await remindersRes.json()).reminders || [];
  const hospitals = (await hospitalsRes.json()).hospitals || [];

  reminderList.innerHTML = reminders
    .map(
      (item) => `
        <li>
          <span><strong>${item.medicine}</strong><br />${item.time}</span>
          <span>${item.days}</span>
        </li>
      `
    )
    .join('');

  hospitalList.innerHTML = hospitals
    .map(
      (hospital) => `
        <div class="hospital-card">
          <h3>${hospital.name}</h3>
          <p>${hospital.specialty}</p>
          <small>Distance: ${hospital.distance}</small>
        </div>
      `
    )
    .join('');
}

symptomForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const symptoms = document.getElementById('symptoms').value;
  const age = document.getElementById('age').value;
  const language = document.getElementById('language').value;

  if (!symptoms.trim()) {
    resultBox.classList.remove('empty');
    resultBox.innerHTML = '<strong>Please enter your symptoms.</strong>';
    return;
  }

  resultBox.classList.remove('empty');
  resultBox.innerHTML = 'Checking symptoms...';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symptoms, age, language })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || 'Unable to assess symptoms');
    }

    const guide = data.analysis;
    resultBox.innerHTML = `
      <p><strong>Diagnosis:</strong> ${guide.diagnosis}</p>
      <p><strong>Severity:</strong> ${guide.severity}</p>
      <p><strong>Advice:</strong> ${guide.advice}</p>
      <p><strong>Next step:</strong> ${guide.next_step}</p>
    `;
  } catch (error) {
    resultBox.innerHTML = `<strong>Error:</strong> ${error.message}`;
  }
});

document.getElementById('sosButton').addEventListener('click', () => {
  resultBox.classList.remove('empty');
  resultBox.innerHTML = `
    <p><strong>Emergency SOS:</strong> Call local emergency services immediately.</p>
    <p>Nearby support: District General Hospital or the nearest community health center.</p>
  `;
});

loadStaticContent();
