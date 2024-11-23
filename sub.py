import os
import logging
import asyncio
import aiohttp
import requests
from PIL import Image
from pyrogram import Client, filters
import praw
import redgifs
from config import *
from database import *
from typing import List, Dict, Optional
from datetime import datetime

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("Reddit.log"),  # Log to file
        logging.StreamHandler()            # Log to console
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

# Reddit API credentials
reddit = praw.Reddit(
    client_id="SFSkzwY_19O3mOsbuwukqg",
    client_secret="ZDGonQJlJHIIz59ubKv-U8Dyho_V2w",
    password="hatelenovo",
    user_agent="testscript by u/Severe_Asparagus_103",
    username="Severe_Asparagus_103",
    check_for_async=False
)

# MongoDB setup
database_name = "Spidydb"
db = connect_to_mongodb(DATABASE, database_name)
collection_name = COLLECTION_NAME

# Pyrogram client
app = Client("SpidyReddit", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=100)

# Utilities
def check_db(db, collection_name, url):
    """Check if a URL exists in the database."""
    # Implement your database check logic here
    return False  # Placeholder logic

def insert_document(db, collection_name, document):
    """Insert a document into the database."""
    # Implement your database insert logic here
    pass

def download_and_compress_image(img_url: str, save_path="compressed.jpg"):
    """Download and compress an image."""
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            with Image.open(save_path) as img:
                if img.mode == "RGBA":  # Convert RGBA to RGB
                    img = img.convert("RGB")
                img.save(save_path, "JPEG", quality=85)
            return save_path
    except Exception as e:
        logging.error(f"Failed to download or compress image: {e}")
        return None

async def download_redgif(link: str) -> Optional[str]:
    """Download a Redgif video."""
    try:
        api = redgifs.API()
        api.login()
        gif_id = link.split("/")[-1].split('#')[0]
        hd_url = api.get_gif(gif_id).urls.hd
        file_path = f"downloads/{gif_id}.mp4"
        os.makedirs("downloads", exist_ok=True)
        async with aiohttp.ClientSession() as session:
            async with session.get(hd_url) as response:
                if response.status == 200:
                    with open(file_path, "wb") as file:
                        file.write(await response.read())
        return file_path
    except Exception as e:
        logging.error(f"Error downloading Redgif: {e}")
        return None

def escape_markdown(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    escape_chars = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in escape_chars else char for char in text)

# Reddit Feed Fetcher
class RedditFeedFetcher:
    def __init__(self, reddit_client: praw.Reddit):
        self.reddit = reddit_client

    async def fetch_subreddit_posts(self, subreddit_list: List[str], limit: int = 20) -> List[Dict]:
        """Fetch posts from multiple subreddits."""
        posts = []
        try:
            subreddit_string = "+".join(subreddit_list)
            for submission in self.reddit.subreddit(subreddit_string).hot(limit=limit):
                post_data = await self._process_submission(submission)
                if post_data:
                    posts.append(post_data)
        except Exception as e:
            logging.error(f"Error fetching subreddit posts: {e}")
        return posts

    async def _process_submission(self, submission) -> Optional[Dict]:
        """Process a single Reddit submission."""
        try:
            if check_db(db, collection_name, submission.url):
                return None

            post_data = {
                "id": submission.id,
                "title": submission.title,
                "url": submission.url,
                "subreddit": submission.subreddit.display_name,
                "author": submission.author.name if submission.author else "[deleted]",
                "created_utc": datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                "media_url": None,
                "thumbnail": submission.thumbnail if submission.thumbnail != "self" else None,
            }

            if hasattr(submission, "is_gallery") and submission.is_gallery:
                if hasattr(submission, "media_metadata"):
                    post_data["media_url"] = [
                        item["s"]["u"] for item in submission.media_metadata.values() if item["e"] == "Image"
                    ]
            elif "redgifs.com" in submission.url:
                post_data["media_url"] = submission.url
            elif submission.url.endswith((".jpg", ".jpeg", ".png", ".gif")):
                post_data["media_url"] = submission.url
            elif hasattr(submission, "is_video") and submission.is_video:
                if hasattr(submission, "media"):
                    post_data["media_url"] = submission.media["reddit_video"]["fallback_url"]

            return post_data if post_data["media_url"] else None
        except Exception as e:
            logging.error(f"Error processing submission: {e}")
            return None

# Main Processing
async def handle_media(url: str, post_data: Dict):
    """Handle media download and send to Telegram."""
    try:
        caption = (
            f"*{escape_markdown(post_data['title'])}*\n\n"
            f"📍 *Subreddit*: r/{escape_markdown(post_data['subreddit'])}\n"
            f"👤 *Author*: u/{escape_markdown(post_data['author'])}\n"
            f"📅 *Uploaded*: {post_data['created_utc']}\n"
            f"[Original Post]({post_data['url']})"
        )

        thumbnail = post_data.get("thumbnail")

        if url.endswith((".jpg", ".jpeg", ".png")):
            local_path = download_and_compress_image(url)
            if local_path:
                await app.send_photo(LOG_ID, photo=local_path, caption=caption, parse_mode="MarkdownV2")
        elif "redgif" in url:
            video_path = await download_redgif(url)
            if video_path:
                await app.send_video(
                    LOG_ID,
                    video=video_path,
                    thumb=thumbnail,
                    caption=caption,
                    parse_mode="MarkdownV2"
                )
        insert_document(
            db,
            collection_name,
            {
                "URL": url,
                "title": post_data["title"],
                "subreddit": post_data["subreddit"],
                "author": post_data["author"],
                "created_utc": post_data["created_utc"],
                "original_url": post_data["url"],
                "thumbnail": thumbnail
            }
        )
    except Exception as e:
        logging.error(f"Error handling media: {e}")

async def process_and_upload(post_data: Dict):
    """Process and upload media to Telegram."""
    try:
        if isinstance(post_data["media_url"], list):
            for url in post_data["media_url"]:
                await handle_media(url, post_data)
        else:
            await handle_media(post_data["media_url"], post_data)
    except Exception as e:
        logging.error(f"Error processing post {post_data['id']}: {e}")

# Main Function
async def main():
    fetcher = RedditFeedFetcher(reddit)
    subreddits = ["BlowJob", "javover30", "jav", "nsfw", "porn"]
    async with app:
        while True:
            try:
                posts = await fetcher.fetch_subreddit_posts(subreddits, limit=10)
                for post in posts:
                    await process_and_upload(post)
                await asyncio.sleep(300)  # Wait 5 minutes before fetching again
            except Exception as e:
                logging.error(f"Main loop error: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    app.run(main())
