import os
import json
import praw
import spacy
import pymongo
import numpy as np
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Reddit API authentication details
reddit = praw.Reddit(
    client_id="8guwEFqGx4pUlbsgb2QuGw",
    client_secret="x_UdlrkW6RCcNU2mngMgnWDL0S_2Rg",
    user_agent="abortion_law_scraper",
)

# Initialize the SentenceTransformer model (for any additional embeddings)
model = SentenceTransformer('all-MiniLM-L6-v2')
# Load the pre-trained NER model from spaCy
nlp = spacy.load('en_core_web_sm')

# MongoDB connection setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["intelliguard_db"]
collection = db["policies"]

SIMILARITY_THRESHOLD = 0.4

def find_policy(query_text):
    """
    Find the most similar policy based on the query text (e.g., post or comment text).
    :param query_text: The query text for finding matching policies
    :return: A list of most similar policies
    """
    query_embedding = model.encode(query_text)
    policies = collection.find()

    matched_policies = []

    for policy in policies:

        stored_embedding = np.array(policy['vector'])
        similarity = cosine_similarity([query_embedding], [stored_embedding])[0][0]

        if similarity > SIMILARITY_THRESHOLD:
            matched_policies.append({
                "law_id": policy["law_id"],
                "text": policy["text"],
                "similarity": similarity,
                "entities": policy["entities"],
            })

    matched_policies = sorted(matched_policies, key=lambda x: x["similarity"], reverse=True)[:3]

    return matched_policies

def apply_ner(text):
    """
    Apply Named Entity Recognition (NER) to the given text to extract entities.
    :param text: The text to process with NER
    :return: A list of entities found in the text
    """
    doc = nlp(text)
    entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in ["LAW", "ORG", "GPE", "PERSON", "PRODUCT"]]
    return entities

def search_reddit_posts(query, subreddit="all", limit=10, num_comments=3, sort_by="relevant"):
    """
    Search posts in the specified subreddit
    :param num_comments: Number of comments to fetch
    :param query: Search keyword
    :param subreddit: Target subreddit (default is 'all')
    :param limit: Limit on the number of posts to fetch
    :return: A list of posts with their details
    """
    results = []
    seen_posts = set()
    post_count = 0
    global_id = 1

    for submission in reddit.subreddit(subreddit).search(query, sort=sort_by):
        # Create a unique key based on title and content
        post_key = (submission.title.lower(), submission.selftext.lower())

        # Skip the post if its title and content have already been seen
        if post_key in seen_posts:
            continue

        seen_posts.add(post_key)

        matched_policies = []
        entities = apply_ner(submission.title + " " + submission.selftext)
        for ent_text, ent_label in entities:
            matched_policies.extend(find_policy(ent_text))

        post_data = ({
            "id": f"P{global_id:03d}",  # P001, P002, P003...
            "type": "post",
            "text": submission.title + " " + submission.selftext,
            "entities": entities,
            "author": submission.author.name if submission.author else "deleted",
            "time": datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "url": submission.url,
            "policies": matched_policies,
            "label": "related" if matched_policies else "unverified"
        })
        results.append(post_data)
        global_id += 1

        comments = get_top_comments(submission, num_comments, global_id)
        results.extend(comments)
        global_id += len(comments)

        post_count += 1
        if post_count >= limit:
            break

    return results

def get_top_comments(submission, num_comments, start_id):
    """
    Get some top comments under a post
    :param submission: Reddit submission object
    :param num_comments: Number of comments to fetch
    :return: A list of comment bodies
    """
    submission.comments.replace_more(limit=0)  # Handle 'More Comments' button
    comments = []
    for i, comment in enumerate(submission.comments.list()[:num_comments]):

        matched_policies = []
        comment_text = comment.body
        entities = apply_ner(comment_text)
        for ent_text, ent_label in entities:
            matched_policies.extend(find_policy(ent_text))

        comments_data = ({
            "id": f"P{start_id + i:03d}",
            "type": "comment",
            "text": comment.body,
            "entities": entities,
            "author": comment.author.name if comment.author else "deleted",
            "time": datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "url": f"https://www.reddit.com{comment.permalink}",
            "policies": matched_policies,
            "label": "related" if matched_policies else "unverified"
        })
        comments.append(comments_data)
    return comments

def save_posts_to_jsonl(posts, filename, append=False):
    """
    Save the scraped posts to a JSON Lines file
    :param posts: List of posts to save
    :param filename: Name of the file to save posts
    """

    output_dir = os.path.dirname(filename)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    mode = "a" if append else "w"
    with open(filename, "w", encoding="utf-8") as file:
        for post in posts:
            # Write each post as a JSON object on a new line
            json.dump(post, file, ensure_ascii=False, separators=(",", ":"))
            file.write("\n")