"""Web3 client for interacting with Base L2."""

import os
import time
from decimal import Decimal
from typing import Any, Dict, List, Optional

import click
from dotenv import load_dotenv
from decimal import Decimal

from requests import HTTPError
from web3 import Web3
from web3.contract import Contract

from src.basescan_client import BaseScanClient
from src.telegram_notifier import TelegramNotifier

# Load environment variables
load_dotenv()


class Web3Client:
    """Client for interacting with Base L2."""

    def __init__(self):
        """Initialize Web3 client with Base L2 connection."""
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("BASE_RPC_URL")))
        self._last_block = None
        self.contract_abi = None
        self.contract_address = None
        self.basescan_client = BaseScanClient()

    def is_connected(self) -> bool:
        """Check if connected to Base L2."""
        return self.w3.is_connected()

    def get_latest_block(self) -> int:
        """Get the latest block number."""
        return self.w3.eth.block_number

    def get_contract_events(self, contract_address: str, from_block: Optional[int] = None, to_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all events for a specific contract."""
        if not self.w3.is_address(contract_address):
            raise ValueError("Invalid contract address")

        # If no from_block specified, use the last 1000 blocks as default range
        if from_block is None:
            latest = self.w3.eth.block_number
            from_block = max(0, latest - 1000)

        # If no to_block specified, use the latest block
        if to_block is None:
            to_block = self.w3.eth.block_number

        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Fetch logs from the blockchain
                logs = self.w3.eth.get_logs({"fromBlock": from_block, "toBlock": to_block, "address": contract_address})

                # Process logs
                events = []
                for log in logs:
                    event = {
                        "transactionHash": log["transactionHash"].hex(),
                        "blockHash": log["blockHash"].hex(),
                        "topics": [topic.hex() for topic in log["topics"]],
                        "data": log["data"],
                        "logIndex": log["logIndex"],
                        "blockNumber": log["blockNumber"],
                    }

                    events.append(event)

                return events

            except HTTPError as e:
                if e.response.status_code == 503:
                    if attempt < max_retries - 1:  # don't sleep on last attempt
                        print(f"Server unavailable, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # exponential backoff
                        continue
                raise  # re-raise the exception if we're out of retries or it's not a 503

        return []  # return empty list if all retries failed

    def get_token_decimals(self, contract: Contract) -> int:
        """
        Fetch the number of decimals for an ERC20 token using the ABI loaded in the w3 client.

        Parameters:
            w3 (Web3): The Web3 instance with the ABI already loaded.
            contract (Contract): The contract instance.

        Returns:
            int: The number of decimals for the token.
        """
        try:
            # Call the decimals function
            decimals = contract.functions.decimals().call()
            return decimals
        except Exception as e:
            raise ValueError(f"Failed to fetch decimals for contract {contract.address}: {str(e)}") from e

    def get_contract_swaps(self, contract: Contract, from_block: Optional[int] = None, to_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all Swap events facilitated by the contract. This is used for realtime monitoring and historical analysis.

        Args:
            contract (Contract): The Web3 contract instance to query events from.
            from_block (Optional[int]): Starting block number for the event query. Defaults to (latest - 1000) if None.
            to_block (Optional[int]): Ending block number for the event query. Defaults to latest block if None.

        Returns:
            List[Dict[str, Any]]: List of swap events with standardized fields.
        """
        if not self.w3.is_address(contract.address):
            raise ValueError("Invalid contract address")

        # Set default block range
        latest_block = self.w3.eth.block_number
        from_block = from_block if from_block is not None else max(0, latest_block - 1000)
        to_block = to_block if to_block is not None else latest_block

        # Validate the presence of the Swap event in the contract's ABI
        if not hasattr(contract.events, "Swap"):
            click.echo(f"Swap event not found in the ABI for contract {contract.address}")
            return []

        # Fetch token0 and token1 addresses and set up contracts
        try:
            token0_address = contract.functions.token0().call()
            token1_address = contract.functions.token1().call()

            # Load token contract ABIs
            token0_contract = self.basescan_client.load_contract(token0_address)
            token1_contract = self.basescan_client.load_contract(token1_address)

            # Fetch token decimals and names
            decimals0 = token0_contract.functions.decimals().call()
            decimals1 = token1_contract.functions.decimals().call()
            token0_name = token0_contract.functions.name().call()
            token1_name = token1_contract.functions.name().call()

            # Check if either token is WETH
            is_token0_weth = token0_name.lower() == "wrapped ether" or token0_name.lower() == "weth"
            is_token1_weth = token1_name.lower() == "wrapped ether" or token1_name.lower() == "weth"

        except Exception as e:
            raise RuntimeError(f"Error initializing token contracts: {str(e)}")

        # Get the Swap event logs
        swap_event = contract.events.Swap()
        try:
            click.echo(f"Fetching Swap event logs from block {from_block} to {to_block}")
            logs = swap_event.get_logs(from_block=from_block, to_block=to_block)
        except Exception as e:
            raise RuntimeError(f"Error fetching Swap event logs: {str(e)}")

        swaps = []
        for log in logs:
            try:
                args = log.args
                swap_data = {}

                # Handle Uniswap V3 style events (amount0 and amount1)
                if hasattr(args, "amount0") and hasattr(args, "amount1"):
                    amount0_raw = args.amount0
                    amount1_raw = args.amount1

                    # Convert amounts to human-readable decimals
                    amount0 = Decimal(amount0_raw) / Decimal(10**decimals0)
                    amount1 = Decimal(amount1_raw) / Decimal(10**decimals1)

                    if is_token0_weth:
                        direction = "BUY" if amount0_raw < 0 else "SELL"
                        if direction == "BUY":
                            amount0 = -(Decimal(amount0_raw) / Decimal(10**decimals0))
                            amount1 = abs(Decimal(amount1_raw) / Decimal(10**decimals1))
                        else:
                            amount0 = abs(Decimal(amount0_raw) / Decimal(10**decimals0))
                            amount1 = -(Decimal(amount1_raw) / Decimal(10**decimals1))
                    elif is_token1_weth:
                        direction = "SELL" if amount1_raw < 0 else "BUY"
                        if direction == "BUY":
                            amount0 = abs(Decimal(amount0_raw) / Decimal(10**decimals0))
                            amount1 = -(Decimal(amount1_raw) / Decimal(10**decimals1))
                        else:
                            amount0 = -(Decimal(amount0_raw) / Decimal(10**decimals0))
                            amount1 = abs(Decimal(amount1_raw) / Decimal(10**decimals1))
                    else:
                        click.echo(f"Unknown token pair: {token0_name} and {token1_name}")
                        continue

                    # Add direction to swap_data
                    swap_data["direction"] = direction

                    # Prepare swap data for V3 style events
                    swap_data.update(
                        {
                            "amount0": str(amount0),
                            "amount1": str(amount1),
                            "direction": direction,
                            "token0_name": token0_name,
                            "token1_name": token1_name,
                        }
                    )

                # Handle Uniswap V2 style events (amount0In, amount1In, etc.)
                elif all(hasattr(args, attr) for attr in ["amount0In", "amount1In", "amount0Out", "amount1Out"]):
                    amount0In = Decimal(args.amount0In) / Decimal(10**decimals0)
                    amount1In = Decimal(args.amount1In) / Decimal(10**decimals1)
                    amount0Out = Decimal(args.amount0Out) / Decimal(10**decimals0)
                    amount1Out = Decimal(args.amount1Out) / Decimal(10**decimals1)

                    direction = "token0 to token1" if amount0In > 0 and amount1Out > 0 else "token1 to token0"

                    # Prepare swap data for V2 style events
                    swap_data.update(
                        {
                            "amount0In": str(amount0In),
                            "amount1In": str(amount1In),
                            "amount0Out": str(amount0Out),
                            "amount1Out": str(amount1Out),
                            "direction": direction,
                            "token0_name": token0_name,
                            "token1_name": token1_name,
                        }
                    )

                # Add common fields
                swap_data.update(
                    {
                        "transactionHash": log.transactionHash.hex(),
                        "blockHash": log.blockHash.hex(),
                        "blockNumber": log.blockNumber,
                        "logIndex": log.logIndex,
                        "sender": getattr(args, "sender", None) or "N/A",
                        "recipient": getattr(args, "recipient", None) or "N/A",
                    }
                )

                swaps.append(swap_data)

            except Exception as e:
                swaps.append(
                    {
                        "error": str(e),
                        "transactionHash": log.transactionHash.hex() if hasattr(log, "transactionHash") else "N/A",
                    }
                )

        return swaps

    def print_swap_event_details(self, event: Dict[str, Any]):
        """Print swap event details and send to Telegram."""
        # Create message for both console and Telegram
        if "error" in event:
            message = f"Error decoding event: {event['error']} (Transaction: {event['transactionHash']})"
        else:
            # Common fields
            transaction_hash = event.get("transactionHash", "N/A")
            sender = event.get("sender", "N/A")
            recipient = event.get("recipient", "N/A")
            direction = event.get("direction", "N/A")
            token0_name = event.get("token0_name", "Unknown")
            token1_name = event.get("token1_name", "Unknown")

            # Build message with HTML formatting for Telegram
            message = (
                f"🔄 <b>New Swap Event</b>\n\n"
                f"📝 <b>Transaction:</b> https://basescan.org/tx/{transaction_hash}\n"
                f"👤 <b>Sender:</b> https://basescan.org/address/{sender}\n"
                f"📮 <b>Recipient:</b> https://basescan.org/address/{recipient}\n"
            )

            # Add amounts based on event type
            if "amount0" in event:
                message += f"💱 <b>{token0_name}:</b> {event['amount0']} ({token0_name})\n" f"💱 <b>{token1_name}:</b> {event['amount1']} ({token1_name})\n"
            else:
                message += (
                    f"📥 <b>{token0_name} In:</b> {event.get('amount0In', 'N/A')} ({event.get('token0_name', 'Unknown')})\n"
                    f"📥 <b>{token1_name} In:</b> {event.get('amount1In', 'N/A')} ({event.get('token1_name', 'Unknown')})\n"
                    f"📤 <b>{token0_name} Out:</b> {event.get('amount0Out', 'N/A')} ({event.get('token0_name', 'Unknown')})\n"
                    f"📤 <b>{token1_name} Out:</b> {event.get('amount1Out', 'N/A')} ({event.get('token1_name', 'Unknown')})\n"
                )

            message += f"↔️ <b>Direction:</b> {direction}"

        # Print to console
        click.echo("\nSwap Event Details:")
        click.echo("--------------------------------------")
        click.echo(message.replace("<b>", "").replace("</b>", ""))
        click.echo("--------------------------------------")

        # Send to Telegram
        try:
            notifier = TelegramNotifier()
            notifier.send_message(message)
        except Exception as e:
            click.echo(f"Failed to send Telegram notification: {str(e)}")
