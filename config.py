import os
import logging
from dotenv import load_dotenv

load_dotenv()

class ConfigValidationError(Exception):
    pass

class Config(object):
    LOG_FORMAT = os.getenv("LOG_FORMAT") or '%(asctime)s - %(levelname)s - %(message)s \t - %(name)s (%(filename)s).%(funcName)s(%(lineno)d) '
    LOG_LEVEL = os.getenv("LOG_LEVEL") or 'INFO'
    APPNAME = os.getenv("APPNAME") or 'Truth Social Monitor'
    ENV = os.getenv("ENV") or "DEV"
    REPEAT_DELAY = int(os.getenv("REPEAT_DELAY") or 300)  # 5 minutes default

    # Discord configuration
    DISCORD_NOTIFY = os.getenv("DISCORD_NOTIFY", 'True').lower() == 'true'
    DISCORD_USERNAME = os.getenv("DISCORD_USERNAME") or "Truth Social Bot"
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
    
    # MongoDB configuration
    MONGO_DBSTRING = os.getenv("MONGO_DBSTRING")
    MONGO_DB = os.getenv("MONGO_DB") or "truthsocial"
    MONGO_COLLECTION = os.getenv("MONGO_COLLECTION") or "posts"

    # Truth Social configuration
    TRUTH_USERNAME = os.getenv("TRUTH_USERNAME")
    TRUTH_INSTANCE = os.getenv("TRUTH_INSTANCE") or "truthsocial.com"
    
    # Request configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT") or 30)
    MAX_RETRIES = int(os.getenv("MAX_RETRIES") or 3)

    # ScrapeOps configuration
    SCRAPEOPS_API_KEY = os.getenv("SCRAPEOPS_API_KEY")
    SCRAPEOPS_ENABLED = os.getenv("SCRAPEOPS_ENABLED", "True").lower() == "true"
    SCRAPEOPS_NUM_RETRIES = int(os.getenv("SCRAPEOPS_NUM_RETRIES") or 3)
    SCRAPEOPS_COUNTRY = os.getenv("SCRAPEOPS_COUNTRY") or "us"

    def __init__(self):
        self.validate_config()

    def validate_config(self):
        """Validate required configuration settings"""
        errors = []

        if not self.TRUTH_USERNAME:
            errors.append("TRUTH_USERNAME is required")

        if self.DISCORD_NOTIFY:
            if not self.DISCORD_WEBHOOK_URL:
                errors.append("DISCORD_WEBHOOK_URL is required when DISCORD_NOTIFY is enabled")

        if not self.MONGO_DBSTRING:
            errors.append("MONGO_DBSTRING is required")

        if self.SCRAPEOPS_ENABLED and not self.SCRAPEOPS_API_KEY:
            errors.append("SCRAPEOPS_API_KEY is required when SCRAPEOPS_ENABLED is true")

        if errors:
            raise ConfigValidationError("\n".join(errors))

        return True
