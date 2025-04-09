import nltk
import fitz  # PyMuPDF
import spacy
import pymongo
from sentence_transformers import SentenceTransformer


nltk.download('punkt')

# Initialize the SentenceTransformer model (for any additional embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')
# Load the pre-trained NER model from spaCy
nlp = spacy.load('en_core_web_sm')

# MongoDB connection setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["intelliguard_db"]
collection = db["policies"]

try:
    # Try to fetch a count of documents in the collection to check the connection
    count = collection.count_documents({})
    print(f"Connected to MongoDB. There are {count} documents in the collection.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

def generate_law_id():
    """
    Generate a unique law_id based on the existing documents in the MongoDB collection.
    :return: A string representing the law_id (e.g., 'L001', 'L002', ...).
    """
    latest_document = collection.find().sort("law_id", pymongo.DESCENDING).limit(1)
    if collection.count_documents({}) > 0:
        latest_law_id = latest_document[0]["law_id"]
        return f"L{int(latest_law_id[1:]) + 1:03d}"
    else:
        return "L001"

def extract_text(file_path):
    """
    Extract text from a PDF file.
    :param pdf_path: The path to the PDF file.
    :return: Extracted text from the PDF.
    """
    doc = fitz.open(file_path)
    text = ""
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text += page.get_text("text")
    return text

def vectorize_text(text):
    """
    Convert text to a vector using SentenceTransformer model.
    :param text: The input text to be vectorized.
    :return: A numpy array representing the embedding of the text.
    """
    return model.encode(text)

def process_file(file_path):
    """
    Process the PDF, extract text, perform NER, vectorize the text, and save to the database.
    :param file_path: Path to the PDF file.
    """
    extracted_text = extract_text(file_path)
    doc = nlp(extracted_text)

    for sentence in doc.sents:
        entities = [(ent.text, ent.label_) for ent in sentence.ents]

        sentence_text = str(sentence)
        vector = vectorize_text(sentence_text)
        law_id = generate_law_id()

        data = {
            "law_id": law_id,
            "type": "policy",
            "text": sentence_text,
            "entities": entities,
            "vector": vector.tolist()
        }

        try:
            collection.insert_one(data)
        except Exception as e:
            print(f"Error inserting document: {e}")