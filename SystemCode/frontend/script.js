const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadMessage = document.getElementById('uploadMessage');

const queryButton = document.getElementById('queryButton');
const queryInput = document.getElementById('queryInput');
const rumorList = document.getElementById('rumors-item');
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

        rumorList.innerHTML = "";
        data.rumor_results.forEach(rumor => {
            const listItem = document.createElement('div');
            listItem.className = 'rumor-item';

            const highlightedDiv = document.createElement('p');
            highlightedDiv.className = 'highlighted-content';
            highlightedDiv.innerHTML = rumor.highlighted_text;

            const nerDiv = document.createElement('p');
            nerDiv.className = 'ner-content';
            nerDiv.innerHTML = rumor.ner || '';

            const authorDiv = document.createElement('p');
            authorDiv.className = 'author-content';
            authorDiv.innerHTML = `<strong>Author:</strong> ${rumor.author || 'Unknown'}`;

            const timeDiv = document.createElement('p');
            timeDiv.className = 'time-content';
            timeDiv.innerHTML = `<strong>Time:</strong> ${rumor.time || 'Not provided'}`;

            const urlDiv = document.createElement('p');
            urlDiv.className = 'url-content';
            urlDiv.innerHTML = `<strong>URL:</strong> <a href="${rumor.link || '#'}" target="_blank">${rumor.link || 'No URL'}</a>`;

            listItem.appendChild(highlightedDiv);
            listItem.appendChild(nerDiv);
            listItem.appendChild(authorDiv);
            listItem.appendChild(timeDiv);
            listItem.appendChild(urlDiv);

            rumorList.appendChild(listItem);
        });

        emotionChart.src = `${BASE_URL}${data.image_url}`;

        rumorsSection.style.display = 'block';
        emotionSection.style.display = 'block';

    } catch (error) {
        queryResult.textContent = "Error: " + error.message;
    }
});