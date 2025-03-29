from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from extracting import extract_text_from_pdf, clean_text, create_json_entry
from scraping import search_reddit_posts, save_posts_to_jsonl

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

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    text = extract_text_from_pdf(filepath)
    text = clean_text(text)

    output_path = '../../Datasets/goverment_truth.jsonl'
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    create_json_entry(text, output_path)

    return jsonify({"message": f"File '{file.filename}' uploaded successfully"}), 200


@app.route('/query', methods=['POST'])
def query():
    """Handle the query input from the text box"""
    user_query = request.json.get('query')
    output_path = "../../Datasets/reddit_contents.jsonl"

    contents = search_reddit_posts(query, limit=10, num_comments=3, sort_by="hot")

    # Save the results to a JSON Lines file
    output_dir = os.path.dirname(output_path)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    save_posts_to_jsonl(contents, filename=output_path)

    return jsonify({"message": f"Received query: {user_query}"}), 200

if __name__ == '__main__':
    app.run(debug=True)