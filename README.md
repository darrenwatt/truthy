# Truth Social Monitor

A Python application that monitors Truth Social posts from specified users and forwards them to Discord.

## Features

- Monitors Truth Social users' posts using Mastodon-compatible API
- Forwards posts to Discord via webhooks
- Stores processed posts in MongoDB to avoid duplicates
- Supports media attachments (images, videos, GIFs)
- Uses ScrapeOps proxy service for reliable scraping
- Rate limiting for Discord notifications
- Automatic retries for failed requests
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- MongoDB instance
- Discord webhook URL
- ScrapeOps API key (optional but recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/truthy.git
   cd truthy
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file with your configuration:
   ```env
   # Logging
   LOG_LEVEL=INFO
   APPNAME="Truth Social Monitor"
   ENV=PROD
   REPEAT_DELAY=300

   # Discord
   DISCORD_NOTIFY=true
   DISCORD_USERNAME="Truth Social Bot"
   DISCORD_WEBHOOK_URL=your_webhook_url_here

   # MongoDB
   MONGO_DBSTRING=mongodb://localhost:27017/
   MONGO_DB=truthsocial
   MONGO_COLLECTION=posts

   # Truth Social
   TRUTH_USERNAME=username_to_monitor
   TRUTH_INSTANCE=truthsocial.com

   # Request Settings
   REQUEST_TIMEOUT=30
   MAX_RETRIES=3

   # ScrapeOps (optional but recommended)
   SCRAPEOPS_ENABLED=true
   SCRAPEOPS_API_KEY=your_api_key_here
   SCRAPEOPS_NUM_RETRIES=3
   SCRAPEOPS_COUNTRY=us

   # FlareSolverr
   FLARESOLVERR_ADDRESS=localhost
   FLARESOLVERR_PORT=8191
   ```

## Usage

Run the monitor:
```bash
python main.py
```

Or using Docker:
```bash
docker build -t truth-social-monitor .
docker run -d --env-file .env truth-social-monitor
```

## Configuration Options

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| LOG_LEVEL | Logging level (INFO, DEBUG, etc.) | INFO |
| REPEAT_DELAY | Time between checks (seconds) | 300 |
| POST_TYPE | Description of post shown in Discord messages | post |
| DISCORD_NOTIFY | Enable Discord notifications | true |
| DISCORD_USERNAME | Bot username in Discord | Truth Social Bot |
| DISCORD_WEBHOOK_URL | Discord webhook URL | Required |
| MONGO_DBSTRING | MongoDB connection string | Required |
| MONGO_DB | MongoDB database name | truthsocial |
| MONGO_COLLECTION | MongoDB collection name | posts |
| TRUTH_USERNAME | Truth Social username to monitor | Required |
| TRUTH_INSTANCE | Truth Social instance domain | truthsocial.com |
| REQUEST_TIMEOUT | Request timeout in seconds | 30 |
| MAX_RETRIES | Max retries for failed requests | 3 |
| SCRAPEOPS_ENABLED | Use ScrapeOps proxy | true |
| SCRAPEOPS_API_KEY | ScrapeOps API key | Required if enabled |
| SCRAPEOPS_NUM_RETRIES | ScrapeOps max retries | 3 |
| SCRAPEOPS_COUNTRY | ScrapeOps proxy country | us |
| FLARESOLVERR_ADDRESS | FlareSolverr service address | localhost |
| FLARESOLVERR_PORT | FlareSolverr service port | 8191 |

## Error Handling

The application includes comprehensive error handling:
- Automatic retries for network failures
- Rate limiting for Discord notifications
- Validation of configuration settings
- Detailed logging of errors and operations
- Safe storage of processed posts

## Contributing

Feel free to submit issues and pull requests.

## License

MIT License
