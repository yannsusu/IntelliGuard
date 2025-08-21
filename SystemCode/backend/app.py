from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os

from extracting import process_file
from scraping import search_reddit_posts, save_posts_to_jsonl
from rumor_detect import predict_rumors
from sentiment_analyst import analyze_and_generate_report

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(os.getcwd(), '../../Documents')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload"""
    uploaded_files = request.files.getlist("files")
    results = []

    for file in uploaded_files:
        if file and file.filename.endswith('.pdf'):
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            try:
                process_file(filepath)
                results.append({"filename": file.filename, "status": "processed"})
            except Exception as e:
                print(f"Error processing {file.filename}: {e}")
                results.append({"filename": file.filename, "status": "error", "error": str(e)})
    return jsonify({"message": "Files uploaded successfully"})

@app.route('/query', methods=['POST'])
def query():
    """Handle the query input from the text box"""
    user_query = request.json.get('query')
    # user_query = ''

    combined_data = "../../Datasets/combined_data.jsonl"
    contents = search_reddit_posts(user_query, limit=10, num_comments=3, sort_by="relevance")
    save_posts_to_jsonl(contents, combined_data, append=False)

    # model_path = "../../Model/bert_v1"
    model_path = "../../Model/bert_rumor"
    predicted = "../../Datasets/prediction_results.jsonl"
    rumors = predict_rumors(model_path, combined_data, predicted)
    print(rumors)
    analyze_and_generate_report(combined_data)

    response = {
        "rumor_results": rumors,
        "image_url": "/sentiment_image"
    }

    return jsonify(response), 200

@app.route('/sentiment_image')
def serve_sentiment_image():
    return send_file('../../Datasets/sentiment.png', mimetype='image/png')

if __name__ == '__main__':
    app.run(debug=True, port=5050)
