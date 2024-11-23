import subprocess
import static_ffmpeg
import os
import logging
import requests
from pyrogram import Client, filters
import praw
import redgifs
from PIL import Image
from config import *
from database import *
import asyncio
import aiohttp
from urllib.parse import urlparse
from typing import List, Dict, Optional

# ... (keep your existing logging and initialization code)

class RedditFeedFetcher:
    def __init__(self, reddit_client: praw.Reddit):
        self.reddit = reddit_client
        self.subreddits = set()  # Track active subreddits
        self.last_fetch_time = {}  # Track last fetch time for each subreddit
        
    async def get_multireddit_feed(self, subreddit_list: List[str], limit: int = 20) -> List[Dict]:
        """
        Get posts from multiple subreddits combined.
        """
        all_posts = []
        
        try:
            # Create a combined subreddit string
            subreddit_string = '+'.join(subreddit_list)
            combined_subreddit = self.reddit.subreddit(subreddit_string)
            
            # Get posts from the combined feed
            async for submission in combined_subreddit.hot(limit=limit):
                post_data = await self._process_submission(submission)
                if post_data:
                    all_posts.append(post_data)
                    
        except Exception as e:
            logging.error(f"Error fetching multi-reddit feed: {e}")
            
        return all_posts
        
    async def get_home_feed(self, limit: int = 20) -> List[Dict]:
        """
        Get posts from Reddit home page / front page
        """
        posts = []
        try:
            async for submission in self.reddit.front.hot(limit=limit):
                post_data = await self._process_submission(submission)
                if post_data:
                    posts.append(post_data)
        except Exception as e:
            logging.error(f"Error fetching home feed: {e}")
        return posts

    async def _process_submission(self, submission) -> Optional[Dict]:
        """
        Process a single Reddit submission and extract relevant data
        """
        try:
            # Skip if already in database
            if check_db(db, COLLECTION_NAME, submission.url):
                return None

            post_data = {
                'id': submission.id,
                'title': submission.title,
                'url': submission.url,
                'subreddit': submission.subreddit.display_name,
                'author': submission.author.name if submission.author else '[deleted]',
                'score': submission.score,
                'created_utc': submission.created_utc,
                'nsfw': submission.over_18,
                'media_type': None,
                'media_url': None
            }

            # Process different types of posts
            if hasattr(submission, "is_gallery") and submission.is_gallery:
                if hasattr(submission, "media_metadata"):
                    media_urls = []
                    for item in submission.media_metadata.values():
                        if item['e'] == 'Image':
                            media_urls.append(item['s']['u'])
                    post_data['media_type'] = 'gallery'
                    post_data['media_url'] = media_urls

            elif "redgifs.com" in submission.url:
                post_data['media_type'] = 'redgif'
                post_data['media_url'] = submission.url

            elif submission.url.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                post_data['media_type'] = 'image'
                post_data['media_url'] = submission.url

            elif hasattr(submission, "is_video") and submission.is_video:
                post_data['media_type'] = 'video'
                if hasattr(submission, "media") and submission.media:
                    post_data['media_url'] = submission.media['reddit_video']['fallback_url']

            return post_data if post_data['media_url'] else None

        except Exception as e:
            logging.error(f"Error processing submission {submission.id}: {e}")
            return None

# Modified main function to use the feed fetcher
async def main():
    """Main function with dynamic feed fetching"""
    feed_fetcher = RedditFeedFetcher(reddit)
    
    # List of subreddits to monitor
    subreddits = ['BlowJob', 'nsfw', 'porn']  # Add your subreddits here
    
    async with app:
        while True:  # Continuous monitoring
            try:
                # Get posts from multiple sources
                home_posts = await feed_fetcher.get_home_feed(limit=10)
                subreddit_posts = await feed_fetcher.get_multireddit_feed(subreddits, limit=20)
                
                # Combine and process all posts
                all_posts = home_posts + subreddit_posts
                
                for post in all_posts:
                    if post and post['media_url']:
                        try:
                            if isinstance(post['media_url'], list):  # Gallery
                                for url in post['media_url']:
                                    result = await process_media(url)
                                    if result:
                                        await send_media_to_telegram(app, result)
                            else:  # Single media
                                result = await process_media(post['media_url'])
                                if result:
                                    await send_media_to_telegram(app, result)
                            
                            # Update database
                            insert_document(db, COLLECTION_NAME, {
                                "URL": post['url'],
                                "title": post['title'],
                                "subreddit": post['subreddit'],
                                "author": post['author'],
                                "created_utc": post['created_utc']
                            })
                            
                        except Exception as e:
                            logging.error(f"Error processing post {post['id']}: {e}")
                
                # Wait before next fetch
                await asyncio.sleep(300)  # 5 minutes delay
                
            except Exception as e:
                logging.error(f"Main loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying

async def send_media_to_telegram(client: Client, media_result: tuple):
    """Send media to Telegram with proper formatting"""
    try:
        if media_result[0] == "photo":
            await client.send_photo(
                LOG_ID,
                photo=media_result[1],
                caption=f"From: {media_result.get('subreddit', 'Unknown')}\n"
                       f"By: {media_result.get('author', 'Unknown')}"
            )
        elif media_result[0] == "video":
            await client.send_video(
                LOG_ID,
                video=media_result[1],
                thumb=media_result[2],
                caption=f"From: {media_result.get('subreddit', 'Unknown')}\n"
                       f"By: {media_result.get('author', 'Unknown')}"
            )
    except Exception as e:
        logging.error(f"Error sending to Telegram: {e}")
    finally:
        # Cleanup files
        for file_path in media_result[1:]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logging.error(f"Cleanup error for {file_path}: {e}")

if __name__ == "__main__":
    app.run(main())
