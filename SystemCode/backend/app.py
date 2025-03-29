from flask import Flask, request, jsonify
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', '..', 'Documents')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filename)

    return jsonify({"message": f"File '{file.filename}' uploaded successfully"}), 200


@app.route('/query', methods=['POST'])
def query():
    """Handle the query input from the text box"""
    user_query = request.json.get('query')
    return jsonify({"message": f"Received query: {user_query}"}), 200


if __name__ == '__main__':
    app.run(debug=True)