"""Telegram notification client."""

import os
from telegram import Bot
from telegram.error import TelegramError
import asyncio
from dotenv import load_dotenv
import click

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
            await self.bot.send_message(chat_id=self.channel_id, text=message, parse_mode="HTML", disable_web_page_preview=True)  # Prevent link previews
            return True
        except TelegramError as e:
            print(f"Failed to send Telegram message to {self.channel_id}: {str(e)}")
            return False

    def send_message(self, message: str, dry_run: bool = False) -> bool:
        """
        Send a message to the Telegram channel.

        Args:
            message (str): The message to send. Can include HTML formatting.
            dry_run (bool): If True, skip sending actual notification

        Returns:
            bool: True if message was sent successfully, False otherwise.
        """
        if dry_run:
            click.echo("[DRY RUN] Would send Telegram message: " + message)
            return False

        return asyncio.run(self._send_message_async(message))
