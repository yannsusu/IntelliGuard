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
    text = re.sub(r'\b[0-9]+\b(?!\))', '', text)
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

def main(pdf_path, output_path):
    """Main function to extract text from PDF and create JSON entries."""
    try:
        text = extract_text_from_pdf(pdf_path)
        text = clean_text(text)
        create_json_entry(text, output_path)
    except Exception as e:
        print(f"An error occurred: {e}")

pdf_path = '../Documents/SB00008F.pdf'
output_path = '../Datasets/goverment_truth.jsonl'

main(pdf_path, output_path)