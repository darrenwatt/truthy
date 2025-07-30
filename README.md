# Truth Social Monitor

A Python application that monitors Truth Social posts from specified users and forwards them to Discord.

## Features

- Monitors Truth Social users' posts using Mastodon-compatible API
- Forwards posts to Discord via webhooks
- Stores processed posts in MongoDB to avoid duplicates
- Supports media attachments (images, videos, GIFs)
- Rate limiting for Discord notifications
- Automatic retries for failed requests
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8 or higher
- MongoDB instance
- Discord webhook URL
- Flaresolverr to run requests through

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/darrenwatt/truthy.git
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

## Configuration

All configuration is handled via environment variables, typically set in a `.env` file at the project root.

### Required Environment Variables

| Variable               | Description                                                      | Example/Default                |
|------------------------|------------------------------------------------------------------|--------------------------------|
| `TRUTH_USERNAME`       | The Truth Social username to monitor                             | `realDonaldTrump`              |
| `MONGO_DBSTRING`       | MongoDB connection string (URI)                                  | `mongodb+srv://...`            |

### Optional Environment Variables

| Variable               | Description                                                      | Example/Default                |
|------------------------|------------------------------------------------------------------|--------------------------------|
| `LOG_FORMAT`           | Python logging format string                                     | See `config.py` for default    |
| `LOG_LEVEL`            | Logging level                                                    | `INFO`                         |
| `APPNAME`              | Application name                                                 | `Truth Social Monitor`         |
| `ENV`                  | Environment name                                                 | `DEV`                          |
| `REPEAT_DELAY`         | Delay between checks (seconds)                                   | `300`                          |
| `DISCORD_NOTIFY`       | Enable Discord notifications (`true`/`false`)                    | `true`                         |
| `DISCORD_USERNAME`     | Username for Discord bot                                         | `Truth Social Bot`             |
| `DISCORD_WEBHOOK_URL`  | Discord webhook URL                                              | *(required if notify enabled)* |
| `MONGO_DB`             | MongoDB database name                                            | `truthsocial`                  |
| `MONGO_COLLECTION`     | MongoDB collection name                                          | `posts`                        |
| `TRUTH_INSTANCE`       | Truth Social instance domain                                     | `truthsocial.com`              |
| `POST_TYPE`            | Type of posts to monitor                                         | `post`                         |
| `REQUEST_TIMEOUT`      | HTTP request timeout (seconds)                                   | `30`                           |
| `MAX_RETRIES`          | Max HTTP request retries                                         | `3`                            |

### Example `.env` file

```env
LOG_LEVEL=INFO
APPNAME="Truth Social Monitor"
ENV=DEV
REPEAT_DELAY=300

DISCORD_NOTIFY=true
DISCORD_USERNAME="Truth Social Bot"
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

MONGO_DBSTRING=mongodb+srv://user:pass@host/db
MONGO_DB=truthsocial
MONGO_COLLECTION=posts

TRUTH_USERNAME=realDonaldTrump
TRUTH_INSTANCE=truthsocial.com
POST_TYPE=post

REQUEST_TIMEOUT=30
MAX_RETRIES=3
```

### Validation

- If `DISCORD_NOTIFY` is `true`, `DISCORD_WEBHOOK_URL` **must** be set.
- `TRUTH_USERNAME` and `MONGO_DBSTRING` are always required.

---
For more details, see the `config.py` file.

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
