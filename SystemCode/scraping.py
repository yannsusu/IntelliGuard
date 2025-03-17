import json
import praw
from datetime import datetime

# Reddit API authentication details
reddit = praw.Reddit(
    client_id="8guwEFqGx4pUlbsgb2QuGw",
    client_secret="x_UdlrkW6RCcNU2mngMgnWDL0S_2Rg",
    user_agent="abortion_law_scraper",
)

def search_reddit_posts(query, subreddit="all", limit=10):
    """
    Search posts in the specified subreddit
    :param query: Search keyword
    :param subreddit: Target subreddit (default is 'all')
    :param limit: Limit on the number of posts to fetch
    :return: A list of posts with their details
    """
    posts = []
    for submission in reddit.subreddit(subreddit).search(query, sort="new", limit=limit):
        posts.append({
            "type": "post",
            "title": submission.title,
            "url": submission.url,
            "author": submission.author.name if submission.author else "deleted",  # Check if author exists
            "time": datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "text": submission.selftext,
            "comments": get_top_comments(submission, num_comments=5)
        })
    return posts

def get_top_comments(submission, num_comments=5):
    """
    Get some top comments under a post
    :param submission: Reddit submission object
    :param num_comments: Number of comments to fetch
    :return: A list of comment bodies
    """
    submission.comments.replace_more(limit=0)  # Handle 'More Comments' button
    comments = []
    for comment in submission.comments.list()[:num_comments]:
        comments.append({
            "type": "comment",
            "author": comment.author.name if comment.author else "deleted",
            "time": datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "text": comment.body,
            "url": f"https://www.reddit.com{comment.permalink}"
        })
    return comments

def save_posts_to_jsonl(posts, filename="reddit_posts.jsonl"):
    """
    Save the scraped posts to a JSON Lines file
    :param posts: List of posts to save
    :param filename: Name of the file to save posts
    """
    with open(filename, "w", encoding="utf-8") as file:
        for post in posts:
            # Write each post as a JSON object on a new line
            json.dump(post, file, ensure_ascii=False)
            file.write("\n")

# Run the scraper
if __name__ == "__main__":
    query = "abortion law USA"
    posts = search_reddit_posts(query, limit=5)  # Limit to 5 posts

    # Save the results to a JSON Lines file
    save_posts_to_jsonl(posts, filename="reddit_posts.jsonl")

    print("Scraped posts saved to 'reddit_posts.jsonl'.")