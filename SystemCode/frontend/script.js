const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const uploadMessage = document.getElementById('uploadMessage');

const queryButton = document.getElementById('queryButton');
const queryInput = document.getElementById('queryInput');
const queryResult = document.getElementById('queryResult');

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
    if (query) {
        const response = await fetch(`${BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ query: query })
        });

        const result = await response.json();
        queryResult.textContent = result.response || "No response from model";
    } else {
        queryResult.textContent = "Please enter a query.";
    }
});