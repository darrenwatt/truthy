import logging
import time
from datetime import datetime, UTC
import requests
from config import Config
from discord_webhook import DiscordWebhook
from pymongo import MongoClient
from urllib.parse import urlencode
from functools import wraps
from ratelimit import limits, sleep_and_retry
import backoff
from bs4 import BeautifulSoup
import re

# Configure logging
config = Config()
logging.basicConfig(
    format=config.LOG_FORMAT,
    level=logging.DEBUG if config.LOG_LEVEL.upper() == 'DEBUG' else logging.INFO,
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Rate limit: 1 request per 2 seconds for Discord
DISCORD_CALLS = 30
DISCORD_PERIOD = 60

@sleep_and_retry
@limits(calls=DISCORD_CALLS, period=DISCORD_PERIOD)
def rate_limited_discord_send(webhook):
    """Execute Discord webhook with rate limiting"""
    return webhook.execute()

@backoff.on_exception(
    backoff.expo,
    (requests.exceptions.RequestException, requests.exceptions.HTTPError),
    max_tries=config.SCRAPEOPS_NUM_RETRIES
)
def make_request(url, headers):
    """Make HTTP request with retry mechanism"""
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {e.response.status_code} for URL {url}")
        logger.error(f"Response headers: {e.response.headers}")
        logger.error(f"Response body: {e.response.text[:500]}")  # First 500 chars of error response
        raise

def get_scrapeops_url(url):
    """Get ScrapeOps proxy URL"""
    payload = {
        'api_key': config.SCRAPEOPS_API_KEY,
        'url': url,
        'country': config.SCRAPEOPS_COUNTRY,
    }
    proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
    return proxy_url

def connect_mongodb():
    """Connect to MongoDB and return the collection"""
    try:
        client = MongoClient(config.MONGO_DBSTRING)
        db = client[config.MONGO_DB]
        collection = db[config.MONGO_COLLECTION]
        logger.info("Successfully connected to MongoDB")
        return collection
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

def is_post_processed(collection, post_id):
    """Check if a post has already been processed"""
    return collection.find_one({"_id": post_id}) is not None

def mark_post_processed(collection, post):
    """Mark a post as processed in MongoDB with additional metadata"""
    try:
        doc = {
            "_id": post["id"],
            "content": post.get("content", ""),
            "created_at": post["created_at"],
            "sent_at": datetime.now(UTC),
            "username": post.get("account", {}).get("username", ""),
            "display_name": post.get("account", {}).get("display_name", ""),
            "media_attachments": [
                {
                    "type": m.get("type"),
                    "url": m.get("url") or m.get("preview_url")
                }
                for m in post.get("media_attachments", [])
                if m.get("type") in ["image", "video", "gifv"]
            ]
        }
        collection.insert_one(doc)
        logger.info(f"Successfully marked post {post['id']} as processed")
    except Exception as e:
        logger.error(f"Error marking post as processed: {e}")
        raise

def send_to_discord(message, media_attachments=None):
    """Send a message to Discord with rate limiting and retries"""
    if not message:
        logger.warning("Empty message, skipping Discord notification")
        return
        
    try:
        webhook = DiscordWebhook(
            url=config.DISCORD_WEBHOOK_URL,
            username=config.DISCORD_USERNAME,
            content=message,
            rate_limit_retry=True,
            delay_between_retries=10  # Wait 10 seconds between retries
        )
        
        # Handle media attachments
        if media_attachments:
            for media in media_attachments:
                if media.get('type') in ['image', 'video', 'gifv']:
                    url = media.get('url') or media.get('preview_url')
                    if url:
                        content, filename = download_media(url)
                        if content and filename:
                            webhook.add_file(file=content, filename=filename)
        
        response = rate_limited_discord_send(webhook)
        status_code = response.status_code
        
        if status_code == 400:
            logger.error(f"Discord 400 error. Message length: {len(message)}")
            logger.error(f"Message content (first 500 chars): {message[:500]}")
            logger.error(f"Response body: {response.text}")
        elif status_code == 429:  # Too Many Requests
            retry_after = response.json().get('retry_after', 5)
            logger.warning(f"Discord rate limit hit, waiting {retry_after} seconds")
            time.sleep(retry_after)
            response = webhook.execute()
            status_code = response.status_code
            
        if status_code not in range(200, 300):
            raise Exception(f"Discord returned status code {status_code}: {response.text}")
            
        logger.info("Successfully sent message to Discord")
    except Exception as e:
        logger.error(f"Error sending message to Discord: {e}")
        raise

def clean_html_and_format(text):
    """Clean HTML tags and format text for Discord"""
    if not text:
        return ""
    
    # Parse HTML with BeautifulSoup
    soup = BeautifulSoup(text, 'html.parser')
    
    # Convert <br> and </p> to newlines
    for br in soup.find_all(['br', 'p']):
        br.replace_with('\n' + br.text)
    
    # Get text and clean up extra whitespace
    text = soup.get_text()
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    # Clean up extra whitespace
    text = re.sub(r' +', ' ', text)
    text = text.strip()
    
    # Convert URLs to clickable format if not already
    url_pattern = r'(?<![\(\[])(https?://\S+)(?![\)\]])'
    text = re.sub(url_pattern, r'<\1>', text)
    
    return text

def format_discord_message(post):
    """Format a post for Discord with media attachments and truncation"""
    if not isinstance(post, dict):
        logger.error(f"Invalid post format: {post}")
        return None

    try:
        created_at = datetime.fromisoformat(post.get('created_at', '').replace('Z', '+00:00'))
        content = post.get('content') or post.get('text', '')
        account = post.get('account', {})
        username = account.get('username') or config.TRUTH_USERNAME
        display_name = account.get('display_name', username)
        
        # Clean and format the content
        content = clean_html_and_format(content)
        
        # Format message parts with exact newlines
        post_type = config.POST_TYPE.capitalize()  # Ensure first letter is capitalized
        header = f"**New {post_type} from {display_name} (@{username})**\n"
        footer = f"\n*Posted at: {created_at.strftime('%B %d, %Y at %I:%M %p %Z')}*"
        
        # Calculate max content length with safety margin
        max_content_length = 1950 - len(header) - len(footer)
        
        # Truncate content if necessary
        if len(content) > max_content_length:
            truncated_length = max_content_length - 3
            content = content[:truncated_length] + "..."
        
        # Build final message without media URLs (they'll be embedded)
        final_message = header + content + footer
        
        # Final safety check
        if len(final_message) > 2000:
            logger.warning(f"Message too long ({len(final_message)} chars), applying emergency truncation")
            return final_message[:1997] + "..."
        
        return final_message
        
    except Exception as e:
        logger.error(f"Error formatting post: {e}")
        return None

def download_media(url):
    """Download media from URL and return the content and filename"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        # Get filename from URL or Content-Disposition header
        filename = url.split('/')[-1].split('?')[0]  # Remove query parameters
        content_type = response.headers.get('content-type', '').lower()
        
        # Ensure proper file extension based on content type
        if 'image/jpeg' in content_type and not filename.lower().endswith(('.jpg', '.jpeg')):
            filename += '.jpg'
        elif 'image/png' in content_type and not filename.lower().endswith('.png'):
            filename += '.png'
        elif 'image/gif' in content_type and not filename.lower().endswith('.gif'):
            filename += '.gif'
        elif 'video/' in content_type and not filename.lower().endswith(('.mp4', '.mov', '.webm')):
            filename += '.mp4'
            
        return response.content, filename
    except Exception as e:
        logger.error(f"Error downloading media from {url}: {e}")
        return None, None

def get_truth_social_posts():
    """Get posts from Truth Social using Mastodon API via ScrapeOps proxy"""
    try:
        # Prepare headers that look like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f'https://{config.TRUTH_INSTANCE}/@{config.TRUTH_USERNAME}',
            'Origin': f'https://{config.TRUTH_INSTANCE}'
        }

        # First get the user ID
        lookup_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/lookup?acct={config.TRUTH_USERNAME}'
        proxy_url = get_scrapeops_url(lookup_url)
        
        response = make_request(proxy_url, headers)
        user_data = response.json()
        
        if not user_data or 'id' not in user_data:
            raise ValueError(f"Could not find user ID for {config.TRUTH_USERNAME}")
            
        user_id = user_data['id']
        logger.debug(f"Found user ID: {user_id}")
        
        # Now get their posts
        posts_url = f'https://{config.TRUTH_INSTANCE}/api/v1/accounts/{user_id}/statuses'
        params = {
            'exclude_replies': 'true',
            'exclude_reblogs': 'true',
            'limit': '40'
        }
        proxy_url = get_scrapeops_url(f"{posts_url}?{urlencode(params)}")
        
        response = make_request(proxy_url, headers)
        posts = response.json()
        
        if not isinstance(posts, list):
            raise ValueError(f"Invalid posts response: {posts}")
            
        logger.info(f"Retrieved {len(posts)} posts")
        return posts
        
    except Exception as e:
        logger.error(f"Error getting Truth Social posts: {e}")
        return []

def make_flaresolverr_request(url, headers=None, params=None):
    """Use FlareSolverr to fetch a URL and return a response-like object."""
    flaresolverr_url = f"http://{config.FLARESOLVERR_ADDRESS}:{config.FLARESOLVERR_PORT}/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 25000,
    }
    if headers:
        payload["headers"] = headers
    if params:
        from urllib.parse import urlencode
        url = url + "?" + urlencode(params)
        payload["url"] = url

    logger.info(f"Making FlareSolverr request: {url} (params={params})")

    try:
        resp = requests.post(flaresolverr_url, json=payload)
        resp.raise_for_status()
        result = resp.json()
        if result.get("status") != "ok":
            logger.error(f"FlareSolverr error: {result}")
            raise Exception(f"FlareSolverr error: {result}")
        response_content = result["solution"]["response"]
        logger.debug(f"FlareSolverr raw response (first 500 chars): {response_content[:500]}")
        # FakeResponse class to handle FlareSolverr response
        class FakeResponse:
            def __init__(self, content):
                self._content = content
            def json(self):
                import json
                from bs4 import BeautifulSoup
                try:
                    return json.loads(self._content)
                except Exception:
                    soup = BeautifulSoup(self._content, "html.parser")
                    pre = soup.find("pre")
                    if pre:
                        try:
                            return json.loads(pre.text)
                        except Exception as e:
                            logger.error(f"Failed to parse JSON from <pre>: {e}")
                            logger.error(f"<pre> content (first 500 chars): {pre.text[:500]}")
                            raise
                    logger.error("No <pre> tag found in FlareSolverr HTML response")
                    logger.error(f"HTML content (first 500 chars): {self._content[:500]}")
                    raise
            @property
            def text(self):
                return self._content
        return FakeResponse(response_content)
    except Exception as e:
        logger.error(f"FlareSolverr request failed for {url}: {e}")
        raise

def main():
    logger.info("Starting Truth Social monitor...")
    
    # Connect to MongoDB
    mongo_collection = connect_mongodb()
    
    while True:
        try:
            # Get posts
            posts = get_truth_social_posts()
            
            # Process posts in reverse chronological order
            for post in sorted(posts, key=lambda x: x.get('created_at', ''), reverse=True):
                # Validate post structure
                if not isinstance(post, dict) or 'id' not in post:
                    logger.warning(f"Invalid post structure: {post}")
                    continue
                    
                # Skip if already processed
                if is_post_processed(mongo_collection, post['id']):
                    logger.debug(f"Post {post['id']} already processed, skipping")
                    continue
                
                logger.info(f"Processing new post {post['id']}")
                
                # Format and send to Discord
                message = format_discord_message(post)
                if message:
                    media_attachments = post.get('media_attachments', [])
                    send_to_discord(message, media_attachments)
                    # Mark as processed only if successfully sent to Discord
                    mark_post_processed(mongo_collection, post)
                
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        
        delay = int(config.REPEAT_DELAY)
        logger.info(f"Waiting {delay} seconds before next check...")
        time.sleep(delay)

if __name__ == "__main__":
    main()
