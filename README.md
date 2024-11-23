📜 SpidyReddit: Your Reddit to Telegram Media Bot

SpidyReddit is a feature-rich bot that automatically fetches media from Reddit (images, videos, and galleries) and sends them to a Telegram chat. Designed to handle NSFW subreddits, Redgifs, and more, it’s the perfect tool for Telegram media automation.


---

🌟 Features

🚀 Fetch from Multiple Subreddits: Supports multiple subreddits and customizable fetch limits.

🖼️ Image, Video, and Gallery Support: Handles media of all types, including Redgifs and Reddit galleries.

🗂️ MongoDB Integration: Prevent duplicates with MongoDB-based URL tracking.

📅 Detailed Post Metadata: Includes subreddit, author, upload date, and original link in the captions.

📷 Thumbnail Handling: Fetches Reddit thumbnails without the need for FFmpeg.

⚡ Efficient and Asynchronous: Built with Pyrogram and asyncio for fast and scalable performance.

🔐 Secure Credentials Management: Uses config.py for API tokens and sensitive data.



---

🛠️ Installation

Follow these steps to get your SpidyReddit bot up and running:

1. Clone the Repository

git clone https://github.com/yourusername/SpidyReddit.git
cd SpidyReddit

2. Install Dependencies

Ensure you have Python 3.10+ installed, then install the required Python packages:

pip install -r requirements.txt

3. Set Up Configuration

Edit the config.py file with your bot credentials:

# config.py

# Pyrogram Telegram API
API_ID = "your_api_id"
API_HASH = "your_api_hash"
BOT_TOKEN = "your_bot_token"

# MongoDB Connection
DATABASE = "mongodb://localhost:27017/"
COLLECTION_NAME = "your_collection"

# Telegram Chat ID
LOG_ID = "your_telegram_chat_id"

4. Obtain API Keys

Reddit: Create a Reddit app at Reddit App Preferences and copy your client_id, client_secret, username, and password.

Telegram: Get your API ID and hash from Telegram Core.


5. Run the Bot

Start the bot with:

python spidyreddit.py


---

🖋️ Usage

Fetch Media from Subreddits

SpidyReddit automatically fetches the latest posts from the specified subreddits every 5 minutes. Customize the subreddits and fetch limits in the main() function:

subreddits = ["BlowJob", "javover30", "jav", "nsfw", "porn"]
posts = await fetcher.fetch_subreddit_posts(subreddits, limit=10)

Handle and Upload Media

The bot supports:

Images: Compressed and sent with captions.

Redgifs Videos: Downloaded and sent with thumbnails.

Galleries: Each image in the gallery is processed individually.



---

📜 Captions

Every post sent to Telegram includes:

Title

Subreddit

Author

Upload Date

Link to the Original Post


Example caption:

**Amazing Post Title**  

📍 **Subreddit**: r/AmazingSubreddit  
👤 **Author**: u/AmazingUser  
📅 **Uploaded**: 2024-11-23 07:00:00  
[🔗 View on Reddit](https://reddit.com/r/examplepost)


---

🚀 Advanced Features

Redgifs Integration: Automatically fetch HD Redgifs videos.

Thumbnail Optimization: Use Reddit’s native thumbnails for better performance.

Duplicate Prevention: Check MongoDB to ensure no media is re-sent.



---

🤔 FAQs

1. How do I change the MongoDB database name?

Edit the following lines in the code:

database_name = "Spidydb"
collection_name = "your_collection"

2. Can I fetch from private subreddits?

Yes! Ensure the Reddit account linked to your bot has access to the subreddit.


---

💡 Tips for Developers

Custom Subreddit List: Modify the subreddits variable in main().

Logging: Check Reddit.log for detailed logs of bot activity.

Error Handling: All errors are logged for debugging.



---

📜 Contribution

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.


---

✨ Future Improvements

🌐 Web Interface: Add a dashboard for easier subreddit management.

📂 Cloud Storage: Upload processed media to cloud storage like AWS or Google Drive.

⏰ Scheduling: Customize fetch intervals per subreddit.



---

📫 Contact

Feel free to reach out if you have questions or need support:

GitHub: MrSpidy

Email: mrspidyxd@gmail.com



---

Make your Telegram channel stand out with SpidyReddit! 🚀

