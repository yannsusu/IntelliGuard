import re
import json
import nltk
import fitz  # PyMuPDF

nltk.download('punkt')

def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file."""
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text

def clean_text(text):
    """Clean extracted text by removing unwanted newlines and extra spaces."""
    text = text.replace("\n", " ")
    text = " ".join(text.split())
    text = re.sub(r'S\.B\.ANo\.[A-Za-z0-9]+', '', text)
    return text

def extract_numbered_text(text):
    """Extract text with numbered items (e.g., (1), (e), etc.)."""
    pattern = r'\([0-9a-zA-Z]+\)[^\(\)]*'
    numbered_items = re.findall(pattern, text)
    return numbered_items

def save_to_jsonl(data, output_path):
    """Save data to a JSONL file."""
    with open(output_path, 'a', encoding='utf-8') as jsonl_file:
        json.dump(data, jsonl_file, ensure_ascii=False)
        jsonl_file.write('\n')

def create_json_entry(text, output_path):
    """Create a JSON entry for each numbered item."""
    numbered_items = extract_numbered_text(text)

    for item in numbered_items:
        item = item.strip()

        if item:  # Ensure the sentence is not empty
            data = {
                "type": "law",
                "text": item,
                "author": "",
                "time": "",
                "url": "",
                "label": "non-rumor"
            }
            save_to_jsonl(data, output_path)