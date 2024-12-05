"""Handles notification of swap events to various outputs (console, telegram, etc.)."""

from typing import Dict, Any
import click
from src.telegram_notifier import TelegramNotifier


class Notifier:
    """Handles formatting and sending notifications."""

    def __init__(self):
        self.telegram_notifier = TelegramNotifier()

    def notify(self, swap_event: Dict[str, Any]) -> None:
        """Send notification for a swap event.

        Args:
            swap_event (Dict[str, Any]): The swap event to notify about
        """
        # Extract dry_run flag from swap event
        dry_run = swap_event.get("dry_run", False)

        message = self._format_message(swap_event)
        self.telegram_notifier.send_message(message, dry_run=dry_run)

    def _format_message(self, event: Dict[str, Any]) -> str:
        """Format the event data into a human-readable message."""
        if "error" in event:
            return f"Error decoding event: {event['error']} (Transaction: {event['transactionHash']})"

        # Common fields
        transaction_hash = event.get("transactionHash", "N/A")
        token0_name = event.get("token0_name", "Unknown")
        token1_name = event.get("token1_name", "Unknown")

        # Build simplified message
        if "amount0" in event:
            message = f"{event['amount0']} {token0_name} → {event['amount1']} {token1_name}\n"
        else:
            message = f"{event.get('amount0In', 'N/A')} {token0_name} → {event.get('amount1Out', 'N/A')} {token1_name}\n"

        message += f"tx: <a href='https://basescan.org/tx/{transaction_hash}'>View</a>"
        return message

    def _print_to_console(self, message: str):
        """Print the message to console."""
        click.echo("\nSwap Event Details:")
        click.echo("--------------------------------------")
        click.echo(message)
        click.echo("--------------------------------------")

    def _send_to_telegram(self, message: str):
        """Send the message to Telegram."""
        try:
            notifier = TelegramNotifier()
            notifier.send_message(message)
        except Exception as e:
            click.echo(f"Failed to send Telegram notification: {str(e)}")
