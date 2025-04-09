from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS
import os

from extracting import process_file
from scraping import search_reddit_posts, save_posts_to_jsonl

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), '../../Documents')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    # file = '../Documents/SB00008F.pdf'

    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    process_file(file_path)

    return jsonify({"message": f"File '{file.filename}' uploaded successfully"}), 200


@app.route('/query', methods=['POST'])
def query():
    """Handle the query input from the text box"""
    user_query = request.json.get('query')
    # user_query = ''

    output_path = "../../Datasets/combined_data.jsonl"
    contents = search_reddit_posts(user_query, limit=3, num_comments=2, sort_by="relevance")
    save_posts_to_jsonl(contents, output_path, append=False)

    return jsonify({"message": f"Received query: {user_query}"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5050)