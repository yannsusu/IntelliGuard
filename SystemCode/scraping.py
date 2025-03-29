import json
import praw
from datetime import datetime

# Reddit API authentication details
reddit = praw.Reddit(
    client_id="8guwEFqGx4pUlbsgb2QuGw",
    client_secret="x_UdlrkW6RCcNU2mngMgnWDL0S_2Rg",
    user_agent="abortion_law_scraper",
)

def search_reddit_posts(query, subreddit="all", limit=10, num_comments=3, sort_by="hot"):
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

    for submission in reddit.subreddit(subreddit).search(query, sort=sort_by):
        # Create a unique key based on title and content
        post_key = (submission.title.lower(), submission.selftext.lower())

        # Skip the post if its title and content have already been seen
        if post_key in seen_posts:
            continue

        seen_posts.add(post_key)

        post_data = ({
            "type": "post",
            "text": submission.title + " " + submission.selftext,
            "author": submission.author.name if submission.author else "deleted",
            "time": datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "url": submission.url,
            "label": "",
        })
        results.append(post_data)

        comments = get_top_comments(submission, num_comments)
        results.extend(comments)

        post_count += 1
        if post_count >= limit:
            break

    return results

def get_top_comments(submission, num_comments):
    """
    Get some top comments under a post
    :param submission: Reddit submission object
    :param num_comments: Number of comments to fetch
    :return: A list of comment bodies
    """
    submission.comments.replace_more(limit=0)  # Handle 'More Comments' button
    comments = []
    for comment in submission.comments.list()[:num_comments]:
        comments_data = ({
            "type": "comment",
            "text": comment.body,
            "author": comment.author.name if comment.author else "deleted",
            "time": datetime.utcfromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
            "url": f"https://www.reddit.com{comment.permalink}",
            "label": "",
        })
        comments.append(comments_data)
    return comments

def save_posts_to_jsonl(posts, filename):
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
    query = "anti abortion law usa"
    output_path = "../Datasets/reddit_contents.jsonl"

    contents = search_reddit_posts(query, limit=10, num_comments=3, sort_by="hot")

    # Save the results to a JSON Lines file
    save_posts_to_jsonl(contents, filename=output_path)

    print(f"Scraped posts and comments saved to '{output_path}'.")