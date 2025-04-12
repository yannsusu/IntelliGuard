const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadMessage = document.getElementById('uploadMessage');

const queryButton = document.getElementById('queryButton');
const queryInput = document.getElementById('queryInput');
const rumorList = document.getElementById('rumors-list');
const emotionChart = document.getElementById('emotion-chart');

const rumorsSection = document.getElementById('rumors-section');
const emotionSection = document.getElementById('emotion-section');

BASE_URL = 'http://127.0.0.1:5050'

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const file = fileInput.files[0];
    if (file && file.type !== 'application/pdf') {
        uploadMessage.textContent = "Only PDF files are allowed.";
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${BASE_URL}/upload`, {
        method: 'POST',
        body: formData
    });

    if (response.ok) {
        const result = await response.json();
        uploadMessage.textContent = result.message || 'Upload successful';
    } else {
        uploadMessage.textContent = 'Upload failed!';
    }
});

queryButton.addEventListener('click', async () => {
    const query = queryInput.value.trim();

    if (!query) {
        alert("Please enter a query.");
        return;
    }

    rumorList.innerHTML = "<li>Loading...</li>";
    emotionChart.src = "";

    try {
        const response = await fetch(`${BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

        rumorList.innerHTML = ""; // Clear previous rumors
        data.rumor_results.forEach(rumor => {
            const listItem = document.createElement('li');
            listItem.textContent = rumor.text;
            rumorList.appendChild(listItem);
        });

        emotionChart.src = `${BASE_URL}${data.image_url}`;

        rumorsSection.style.display = 'block';
        emotionSection.style.display = 'block';

    } catch (error) {
        queryResult.textContent = "Error: " + error.message;
    }
});