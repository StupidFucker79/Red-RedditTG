import os
import logging
import requests
from pyrogram import Client
import praw
from telegraph import Telegraph, exceptions
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

# Configure logging
logging.basicConfig(
    filename='Reddit.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# MongoDB setup
database_name = "Spidydb"
db = connect_to_mongodb(DATABASE, database_name)
collection_name = COLLECTION_NAME

# Telegraph client
telegraph = Telegraph()
telegraph.create_account(short_name='PythonTelegraphBot')

# Pyrogram client
app = Client("SpidyReddit", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, workers=100)

# Get image URLs from a subreddit
async def get_image_urls(subreddit_name):
    image_urls = []
    gif_paths = []
    for submission in reddit.subreddit(subreddit_name).hot(limit=50):  # limit to 50 submissions
        if "gallery" in submission.url:
            submission = reddit.submission(url=submission.url)
            for image_item in submission.media_metadata.values():
                image_urls.append(image_item['s']['u'])
        elif "redgif" in submission.url:
            gif = await download_redgif(submission.url)
            if gif:
                gif_paths.append(gif)
        elif submission.url.startswith("https://i.redd.it"):
            image_urls.append(submission.url)
    return image_urls, gif_paths

# Download and compress image
def download_and_compress_image(img_url, save_path="compressed.jpg"):
    try:
        response = requests.get(img_url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            with Image.open(save_path) as img:
                img.save(save_path)
            return save_path
    except Exception as e:
        logging.error(f"Failed to download or compress image: {e}")
        return None

# Upload an image to Telegraph
def upload_image_to_telegraph(image_path):
    try:
        with open(image_path, 'rb') as f:
            return telegraph.upload_file(f)[0]["src"]
    except exceptions.TelegraphException as e:
        logging.error(f"TelegraphException: {e}")
    except Exception as e:
        logging.error(f"Error uploading to Telegraph: {e}")
    return None

# Upload multiple images to Telegraph page
def upload_content_to_telegraph(title, content):
    try:
        page_content = [{'tag': 'h3', 'children': [title]}] + [{'tag': 'img', 'attrs': {'src': url}} for url in content]
        return telegraph.create_page(title=title, author_name='PythonTelegraphBot', content=page_content)['url']
    except exceptions.TelegraphException as e:
        logging.error(f"TelegraphException: {e}")
    except Exception as e:
        logging.error(f"Error creating Telegraph page: {e}")
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
    subreddit_name = 'pussy'  # replace with your target subreddit
    image_urls, gif_paths = await get_image_urls(subreddit_name)
    uploaded_image_urls = []
    for image_url in image_urls:
        if not check_db(db, collection_name, image_url):
            logging.info(image_url)
            if any(ext in image_url.lower() for ext in ["jpg", "png", "jpeg"]):
                local_image_path = download_and_compress_image(image_url)
                if local_image_path:
                    uploaded_url = upload_image_to_telegraph(local_image_path)
                    if uploaded_url:
                        up_url = f"https://graph.org{uploaded_url}"
                        uploaded_image_urls.append(up_url)
                        await app.send_photo(LOG_ID,photo=local_image_path)
                        result = {"URL": image_url, "Image": up_url}
                        insert_document(db, collection_name, result)
                        os.remove(local_image_path)
                

    if uploaded_image_urls:
        logging.info(f"Uploaded images: {uploaded_image_urls}")
    else:
        logging.error("Failed to upload images to Telegraph.")

# Running the Pyrogram app and async main() properly
if __name__ == "__main__":
    app.run(main())
