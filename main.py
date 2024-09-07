import os
import logging
import requests
from pyrogram import Client
import praw
import redgifs
from PIL import Image
from config import *
from database import *
import asyncio

# Reddit API credentials
reddit = praw.Reddit(
    client_id="SFSkzwY_19O3mOsbuwukqg",
    client_secret="ZDGonQJlJHIIz59ubKv-U8Dyho_V2w",
    password="hatelenovo",
    user_agent="testscript by u/Severe_Asparagus_103",
    username="Severe_Asparagus_103",
    check_for_async=False
)

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("Reddit.log"),  # Log to file
        logging.StreamHandler()  # Log to console
    ]
)

# MongoDB setup
database_name = "Spidydb"
db = connect_to_mongodb(DATABASE, database_name)
collection_name = COLLECTION_NAME


# Pyrogram client
app = Client("SpidyReddit", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=100)

# Get image URLs from a subreddit
async def get_urls(subreddit_name):
    urls = []
    for submission in reddit.subreddit(subreddit_name).hot(limit=20):  # limit to 50 submissions
        if "gallery" in submission.url:
            submission = reddit.submission(url=submission.url)
            for image_item in submission.media_metadata.values():
                urls.append(image_item['s']['u'])
        elif "redgif" in submission.url:
                urls.append(submission.url)
        elif submission.url.startswith("https://i.redd.it"):
            urls.append(submission.url)
    return urls

# Download and compress image
def download_and_compress_image(img_url, save_path="compressed.jpg"):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            with Image.open(save_path) as img:
                # Convert RGBA to RGB if necessary
                if img.mode == "RGBA":
                    img = img.convert("RGB")
                img.save(save_path, "JPEG")
            return save_path
    except Exception as e:
        logging.error(f"Failed to download or compress image: {e}")
        return None


# Download Redgif
async def download_redgif(link):
    try:
        api = redgifs.API()
        api.login()
        gif_id = link.split("/")[-1].split('#')[0]
        hd_url = api.get_gif(gif_id).urls.hd
        file_path = f"{gif_id}.mp4"
        api.download(hd_url, file_path)
        return file_path
    except Exception as e:
        logging.error(f"Error downloading Redgif: {e}")
        return None
    finally:
        api.close()

# Async main function to process subreddit images
async def main():
 async with app:
    subreddit_name = 'braless'  # replace with your target subreddit
    urls = await get_urls(subreddit_name)
    uploaded_urls = []
    for url in urls:
        logging.info(f"Processing URL: {url}")  # This will now print and log
        if not check_db(db, collection_name, url):
            if any(ext in url.lower() for ext in ["jpg", "png", "jpeg"]):
                local_path = download_and_compress_image(url)
                await app.send_photo(LOG_ID, photo=local_path)
            elif "redgif" in url:
                local_path =  await download_redgif(url)
                await app.send_video(LOG_ID, video=local_path)
            if local_path:
                    if True:
                        uploaded_urls.append(url)
                        result = {"URL": url}
                        insert_document(db, collection_name, result)
                        os.remove(local_path)
                        

    if uploaded_urls:
        logging.info(f"Uploaded images: {uploaded_urls}")
    else:
        logging.error("Failed to upload images to Telegraph.")

# Running the Pyrogram app and async main() properly
if __name__ == "__main__":
    app.run(main())
