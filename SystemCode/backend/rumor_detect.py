import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from peft import PeftModel, LoraConfig, get_peft_model

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def load_model(model_path):
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    # lora_config = LoraConfig.from_pretrained(model_path)
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.1,
        task_type="SEQ_CLS"
    )
    model = get_peft_model(model, lora_config)
    model.load_state_dict(torch.load(model_path + "/pytorch_model.bin", map_location=torch.device('cpu')))
    model.eval()

    return model, tokenizer

def predict_batch(model, tokenizer, texts, batch_size=16):

    convert_label = {
        0: "truth",
        1: "rumor",
        2: "unverified"
    }

    predictions = []
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        inputs = tokenizer(batch_texts, padding=True, truncation=True,
                           return_tensors="pt", max_length=512)
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            batch_preds = torch.argmax(logits, dim=1).cpu().tolist()
            batch_probs = torch.nn.functional.softmax(logits, dim=1).cpu().tolist()

        for text, pred, prob in zip(batch_texts, batch_preds, batch_probs):
            predictions.append({
                "id": pred,
                "text": text,
                "label": convert_label.get(pred),
                "confidence": prob[pred],
            })
    return predictions

def enrich_predictions(predictions, original_data):
    for i, item in enumerate(original_data):
        if i < len(predictions):
            predictions[i]["id"] = item.get("id", i)
    return predictions

def save_to_jsonl(data, path):
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def predict_rumors(model_path, input_path):
    data = load_jsonl(input_path)
    texts = [item.get("text", "") for item in data]
    model, tokenizer = load_model(model_path)
    predictions = predict_batch(model, tokenizer, texts)
    enriched = enrich_predictions(predictions, data)
    rumors = [item for item in enriched if item['label'] == 'rumor']
    # save_to_jsonl(enriched, output_path)
    return rumors

if __name__ == "__main__":
    model_path = "../../Model"  # Path to your model
    input_path = "../../Datasets/combined_data.jsonl"
    # output_path = "../../Datasets/prediction_results.jsonl"

    results = predict_rumors(model_path, input_path)
    truth_results = [result for result in results if result['label'] == 'truth']
    rumor_results = [result for result in results if result['label'] == 'rumor']
    unverified_results = [result for result in results if result['label'] == 'unverified']

    truth_count = len(truth_results)
    rumor_count = len(rumor_results)
    unverified_count = len(unverified_results)

    print(f"Truth count: {truth_count}")
    print(f"Rumor count: {rumor_count}")
    print(f"Unverified count: {unverified_count}")