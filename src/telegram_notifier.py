"""Telegram notification client."""

import os
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from dotenv import load_dotenv

load_dotenv()


class TelegramNotifier:
    """Client for sending notifications to Telegram channel."""

    def __init__(self):
        """Initialize Telegram notifier with bot token."""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
        self.channel_id = "@base_tokenbot"
        self.bot = Bot(self.bot_token)

    async def _send_message_async(self, message: str) -> bool:
        """Send message asynchronously."""
        try:
            await self.bot.send_message(chat_id=self.channel_id, text=message, parse_mode="HTML")
            return True
        except TelegramError as e:
            print(f"Failed to send Telegram message: {str(e)}")
            return False

    def send_message(self, message: str) -> bool:
        """
        Send a message to the Telegram channel.

        Args:
            message (str): The message to send. Can include HTML formatting.

        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        return asyncio.run(self._send_message_async(message))
