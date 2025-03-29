import jsonlines
import spacy

# Load data from a JSONL file
def load_data(file_path):
    """
    Load data from a jsonl file.
    :param file_path: Path to the jsonl file.
    :return: List of data objects.
    """
    with jsonlines.open(file_path) as reader:
        return [obj for obj in reader]

# Extract named entities using spaCy's NER model
def extract_entities(text, nlp_model):
    """
    Extract named entities from a given text using the spaCy NER model.
    :param text: The input text for entity extraction.
    :param nlp_model: The spaCy NER model.
    :return: List of entities (text, label).
    """
    doc = nlp_model(text)

    entities = []
    for ent in doc.ents:
        if ent.text.lower() == "years old" or ent.text == "":
            continue

        if ent.text == "Subchapter H" or ent.text == "SUBCHAPTER H. DETECTION":
            entities.append((ent.text, 'LAW'))
        else:
            entities.append((ent.text, ent.label_))

    return entities

# Main function to process data
def main():
    """
    Main function to process and match data, perform NER, and format the results for BERT input.
    """
    # Load the pre-trained NER model from spaCy
    nlp = spacy.load('en_core_web_sm')

    # Load both datasets (correct and uncertain)
    correct_data = load_data('../Datasets/goverment_truth.jsonl')
    uncertain_data = load_data('../Datasets/reddit_contents.jsonl')

    # Process the first 3 items in correct data and extract entities
    print("Correct Data Entities:")
    for i, item in enumerate(correct_data[:3]):  # Limit to the first 3 items
        entities = extract_entities(item['text'], nlp)
        print(f"Text: {item['text']}")
        print(f"Entities: {entities}")
        print("-" * 50)

    # Process the first 3 items in uncertain data and extract entities
    print("Uncertain Data Entities:")
    for i, item in enumerate(uncertain_data[:3]):  # Limit to the first 3 items
        entities = extract_entities(item['text'], nlp)
        print(f"Text: {item['text']}")
        print(f"Entities: {entities}")
        print("-" * 50)

# Run the main function
if __name__ == "__main__":
    main()