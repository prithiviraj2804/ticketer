from curl_cffi import requests
import logging
import re
import asyncio
from typing import List
from datetime import datetime
from config import load_config, Config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TicketMonitor:
    def __init__(self):
        self.config: Config = load_config()
        self.last_check_status = "Not started"
        self.last_check_time = None
        self.is_running = False

    def send_telegram_message(self, message: str):
        """Sends a message to the configured Telegram chat."""
        if self.config.bot_token == "YOUR_BOT_TOKEN" or self.config.chat_id == "YOUR_CHAT_ID":
            logger.warning("Telegram configuration missing. Skipping notification.")
            return

        url = f"https://api.telegram.org/bot{self.config.bot_token}/sendMessage"
        payload = {
            "chat_id": self.config.chat_id,
            "text": message
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")

    def check_tickets(self):
        """Checks the URL for the search texts."""
        logger.info(f"Checking URL: {self.config.url}")
        self.last_check_time = datetime.now()
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Ch-Ua": '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

        try:
            response = requests.get(self.config.url, headers=headers, timeout=30, impersonate="chrome")
            
            if response.status_code == 403:
                logger.error("403 Forbidden encountered.")
                self.send_telegram_message(f"⚠️ 403 FORBIDDEN DETECTED ⚠️\n\nThe bot might be blocked. Pausing checks for a while.\nURL: {self.config.url}")
                self.last_check_status = "403 Forbidden"
                return "403_FORBIDDEN"
            
            response.raise_for_status()
            
            found_matches = []
            for text in self.config.search_texts:
                # Use Regex to find text inside a <span> tag.
                if re.search(r'<span[^>]*>[^<]*' + re.escape(text), response.text):
                    found_matches.append(text)
            
            if found_matches:
                match_str = ", ".join(found_matches)
                logger.info(f"FOUND MATCHES: '{match_str}'")
                self.send_telegram_message(f"🚨 TICKETS AVAILABLE! 🚨\n\nFound the following cinemas:\n{match_str}\n\nLink:\n{self.config.url}")
                self.last_check_status = f"Found: {match_str}"
                return "FOUND"
            else:
                logger.info(f"Not found in booking list.")
                self.last_check_status = "Not Found"
                return "NOT_FOUND"

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL: {e}")
            self.last_check_status = f"Error: {e}"
            return "ERROR"

    async def start_monitoring(self):
        """Starts the background monitoring loop."""
        self.is_running = True
        logger.info("Starting background monitoring loop...")
        
        while self.is_running:
            result = self.check_tickets()
            
            sleep_time = self.config.check_interval
            
            if result == "403_FORBIDDEN":
                # Backoff for longer if 403 encountered to avoid hammering
                sleep_time = 60  # Wait 1 minute
                logger.info(f"Backing off for {sleep_time} seconds due to 403...")
                self.send_telegram_message(f"⚠️ 403 FORBIDDEN DETECTED ⚠️\n\nThe bot might be blocked. Pausing checks for a while.\nURL: {self.config.url}")
            
            await asyncio.sleep(sleep_time)

    def stop_monitoring(self):
        self.is_running = False
        logger.info("Stopping monitoring loop...")
