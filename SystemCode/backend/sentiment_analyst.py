import json
from transformers import pipeline
from collections import Counter
import matplotlib.pyplot as plt

sentiment_pipeline = pipeline("text-classification", model="j-hartmann/emotion-english-distilroberta-base")

def load_jsonl(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]

def analyze_sentiment(data):
    posts_with_sentiment = []
    for item in data:
        result = sentiment_pipeline(item["text"])
        if result and isinstance(result, list) and "label" in result[0]:
            item["emotion_labels"] = result
            item["dominant_emotion"] = result[0]["label"]
            item["dominant_score"] = result[0]["score"]
        else:
            print(f"Skipping item with no valid emotion result: {item}")
            item["dominant_emotion"] = "no emotion"
            item["dominant_score"] = 0.0
        posts_with_sentiment.append(item)
    return posts_with_sentiment

def plot_sentiment_pie_chart(emotion_counter, total_posts):
    labels = list(emotion_counter.keys())
    counts = list(emotion_counter.values())
    colors = plt.get_cmap('tab20').colors

    plt.figure(figsize=(4, 4))
    wedges, texts, autotexts = plt.pie(
        counts,
        labels=labels,
        autopct='%1.1f%%',
        startangle=140,
        colors=colors[:len(labels)],
        textprops=dict(color="black")
    )

    for text in texts:
        text.set_fontsize(10)
    for autotext in autotexts:
        autotext.set_fontsize(9)
        autotext.set_color('white')

    plt.title('Emotion Distribution of Posts', fontsize=12, fontweight='bold')
    plt.axis('equal')
    plt.tight_layout()
    plt.savefig("../../Datasets/sentiment.png")
    plt.close()

def generate_report(posts_with_sentiment):
    emotion_counter = Counter(item['dominant_emotion'] for item in posts_with_sentiment)
    total_posts = len(posts_with_sentiment)

    print("\nEmotion Report:")
    for emotion, count in emotion_counter.items():
        percentage = (count / total_posts) * 100
        print(f"{emotion}: {count} posts ({percentage:.2f}%)")

    plot_sentiment_pie_chart(emotion_counter, total_posts)

def analyze_and_generate_report(input_path):
    data = load_jsonl(input_path)
    posts_with_sentiment = analyze_sentiment(data)
    generate_report(posts_with_sentiment)
    return posts_with_sentiment