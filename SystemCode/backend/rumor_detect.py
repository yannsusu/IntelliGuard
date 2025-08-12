import re
import json
import torch
from pathlib import Path
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification, pipeline
from peft import get_peft_model, PeftConfig, PeftModel
from captum.attr import IntegratedGradients

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


# def load_model(model_path):
#     tokenizer = BertTokenizer.from_pretrained(model_path)
#     peft_config = PeftConfig.from_pretrained(model_path)
#     base_model = BertForSequenceClassification.from_pretrained(peft_config.base_model_name_or_path, num_labels=3)
#     model = get_peft_model(base_model, peft_config)
#     model.load_state_dict(torch.load(model_path + "/pytorch_model.bin", map_location=torch.device('cpu')))
#     model.eval()
#
#     return model, tokenizer

def load_model(model_path):
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)

    return model, tokenizer

# def load_model(model_path):
#     tokenizer = BertTokenizer.from_pretrained(model_path)
#     peft_config = PeftConfig.from_pretrained(model_path)
#
#     base_model = BertForSequenceClassification.from_pretrained(
#         peft_config.base_model_name_or_path,
#         num_labels=2
#     )
#
#     model = get_peft_model(base_model, peft_config)
#
#     model.eval()
#
#     return model, tokenizer

def ner_extract(text):
    if not hasattr(ner_extract, "ner_pipeline"):
        model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(model_name)
        ner_extract.ner_pipeline = pipeline("ner", model=model, tokenizer=tokenizer, aggregation_strategy="simple")

    ner_results = ner_extract.ner_pipeline(text)

    seen = set()
    entities = []
    for entity in ner_results:
        text_span = entity["word"]
        label = entity["entity_group"]
        key = (text_span, label)
        if key not in seen:
            seen.add(key)
            entities.append(f"{text_span} ({label})")

    if entities:
        result_text = "<br><b>Named Entities:</b> "
        result_text += ", ".join(entities)
    else:
        result_text = ""

    return result_text

def ig_highlight(text, model, tokenizer, label_id=1, top_k=5):
    model.eval()

    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    inputs_embeds = model.get_input_embeddings()(input_ids)

    def forward_func(inputs_embeds):
        outputs = model(inputs_embeds=inputs_embeds, attention_mask=attention_mask)
        return outputs.logits[:, label_id]

    ig = IntegratedGradients(forward_func)

    attributions, _ = ig.attribute(inputs=inputs_embeds, return_convergence_delta=True)
    attributions = attributions.sum(dim=-1).squeeze(0).detach()

    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    words = []
    current_word = ""
    current_score = 0
    current_tokens = []

    for tok, score in zip(tokens, attributions):
        if tok in ["[CLS]", "[SEP]", "[PAD]"]:
            continue
        if tok.startswith("##"):
            current_word += tok[2:]
        else:
            if current_word:
                words.append((current_word, current_score / max(len(current_tokens), 1), current_tokens))
            current_word = tok
            current_score = 0
            current_tokens = []
        current_score += score
        current_tokens.append((tok, score))

    if current_word:
        words.append((current_word, current_score / max(len(current_tokens), 1), current_tokens))

    scored_words = [(word, abs(score)) for word, score, _ in words]
    top_words = set([word for word, _ in sorted(scored_words, key=lambda x: x[1], reverse=True)[:top_k]])

    output_tokens = []
    for i, (word, _, token_group) in enumerate(words):
        merged = "".join(tok if not tok.startswith("##") else tok[2:] for tok, _ in token_group)
        is_punct = re.match(r"^[\.,!?/'\";:]+$", merged)
        if word in top_words:
            merged = f"<span style='background-color:rgba(169,169,169,0.3);'>{merged}</span>"
        if i > 0 and not is_punct:
            output_tokens.append(" ")
        output_tokens.append(merged)

    result = "".join(output_tokens).strip()

    def capitalize_sentences(text):
        return re.sub(r'(^|(?<=[\.\?!]\s))([a-z])',
                      lambda m: m.group(1) + m.group(2).upper(), text)

    return capitalize_sentences(result)


def predict_batch(model, tokenizer, texts, data, batch_size=16):

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

        for j, (text, pred, prob) in enumerate(zip(batch_texts, batch_preds, batch_probs)):
            index = i + j
            ner_text = ner_extract(text)
            highlighted_text = ig_highlight(text, model, tokenizer)

            # Get author, time, url from original_data
            author = data[index].get("author", "")
            time = data[index].get("time", "")
            url = data[index].get("url", "")

            result = {
                "id": pred,
                "text": text,
                "highlighted_text": highlighted_text,
                "ner": ner_text,
                "label": convert_label.get(pred),
                "confidence": prob[pred],
                "author": author,
                "time": time,
                "link": url
            }

            predictions.append(result)

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

def predict_rumors(model_path, input_path, output_path):
    data = load_jsonl(input_path)
    texts = [item.get("text", "") for item in data]
    model, tokenizer = load_model(model_path)
    predictions = predict_batch(model, tokenizer, texts, data)
    enriched = enrich_predictions(predictions, data)
    rumors = [item for item in enriched if item['label'] == 'rumor']
    save_to_jsonl(enriched, output_path)
    return rumors

if __name__ == "__main__":
    # model_path = "../../Model/bert_v1"
    model_path = "../../Model/bert_rumor"

    input_path = "../../Datasets/combined_data.jsonl"
    output_path = "../../Datasets/prediction_results.jsonl"

    results = predict_rumors(model_path, input_path, output_path)
    truth_results = [result for result in results if result['label'] == 'truth']
    rumor_results = [result for result in results if result['label'] == 'rumor']
    unverified_results = [result for result in results if result['label'] == 'unverified']

    truth_count = len(truth_results)
    rumor_count = len(rumor_results)
    unverified_count = len(unverified_results)

    print(f"Truth count: {truth_count}")
    print(f"Rumor count: {rumor_count}")
    print(f"Unverified count: {unverified_count}")