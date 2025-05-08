const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadMessage = document.getElementById('uploadMessage');
const loadingMessage = document.getElementById("loadingMessage")
const fileList = document.getElementById("fileList")

const queryButton = document.getElementById('queryButton');
const queryInput = document.getElementById('queryInput');
const emotionChart = document.getElementById('emotion-chart');
const rumorList = document.getElementById('rumors-item');

const rumorsSection = document.getElementById('rumors-section');
const emotionSection = document.getElementById('emotion-section');

BASE_URL = 'http://127.0.0.1:5050'

let selectedFiles = []

fileInput.addEventListener('change', async (e) => {
    const files = Array.from(e.target.files).filter(file => file.type === 'application/pdf');
    if (files.length === 0) {
        uploadMessage.textContent = "Only PDF files are allowed.";
        return;
    }

    const formData = new FormData();
    files.forEach(file => {
        formData.append('files', file);
    });

    uploadMessage.textContent = "Uploading...";
    try {
        const response = await fetch(`${BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            uploadMessage.textContent = result.message || 'Upload successful';

            files.forEach(file => {
                if (!selectedFiles.some(f => f.name === file.name)) {
                    selectedFiles.push(file);
                }
            });

            renderFileList();
        } else {
            uploadMessage.textContent = 'Upload failed!';
        }
    } catch (err) {
        uploadMessage.textContent = 'Upload error: ' + err.message;
    } finally {
        fileInput.value = "";
    }
});

function renderFileList() {
    fileList.innerHTML = "";

    selectedFiles.forEach((file, index) => {
        const row = document.createElement('tr');

        const nameCell = document.createElement('td');
        nameCell.textContent = file.name;
        nameCell.style.padding = '8px';

        const actionCell = document.createElement('td');
        actionCell.style.padding = '8px';

        const removeBtn = document.createElement('button');
        removeBtn.textContent = 'Remove';
        removeBtn.style.backgroundColor = '#d63031';
        removeBtn.style.color = 'white';
        removeBtn.style.border = 'none';
        removeBtn.style.borderRadius = '4px';
        removeBtn.style.cursor = 'pointer';
        removeBtn.style.padding = '4px 8px';

        removeBtn.addEventListener('click', () => {
            selectedFiles.splice(index, 1);
            renderFileList();
        });

        actionCell.appendChild(removeBtn);
        row.appendChild(nameCell);
        row.appendChild(actionCell);
        fileList.appendChild(row);
    });
}

uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (selectedFiles.length === 0) {
        uploadMessage.textContent = "Please select at least one PDF file.";
        return;
    }

    const formData = new FormData();
    selectedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch(`${BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            uploadMessage.textContent = result.message || 'Upload successful';
            renderFileList();
        } else {
            uploadMessage.textContent = 'Upload failed!';
        }
    } catch (err) {
        uploadMessage.textContent = 'Upload error: ' + err.message;
    }
});

queryButton.addEventListener('click', async () => {
    const query = queryInput.value.trim();

    if (!query) {
        alert("Please enter a query.");
        return;
    }

    rumorList.innerHTML = "";
    emotionChart.src = "";
    loadingMessage.style.display = 'block';

    try {
        const response = await fetch(`${BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        const data = await response.json();

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
    uploadMessage.textContent = "Query failed: " + error.message;
    } finally {
        loadingMessage.style.display = 'none';
    }
});