"""Web3 client for interacting with Base L2."""

from typing import Optional, List, Dict, Any
from web3 import Web3
import click
from dotenv import load_dotenv
import os
from decimal import Decimal, getcontext, ROUND_DOWN
import time
from requests import HTTPError
from web3.contract import Contract

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

    def is_connected(self) -> bool:
        """Check if connected to Base L2."""
        return self.w3.is_connected()

    def get_latest_block(self) -> int:
        """Get the latest block number."""
        return self.w3.eth.block_number

    def get_contract_transfers(self, contract: Contract, from_block: Optional[int] = None, to_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all ERC20 Transfer events facilitated by the contract."""
        if not self.w3.is_address(contract.address):
            raise ValueError("Invalid contract address")

        if from_block is None:
            latest = self.w3.eth.block_number
            from_block = max(0, latest - 1000)

        if to_block is None:
            to_block = self.w3.eth.block_number

        # Extract the Transfer event signature from the contract ABI
        transfer_event_signature = "0x" + self.w3.keccak(text="Transfer(address,address,uint256)").hex()

        logs = self.w3.eth.get_logs({"fromBlock": from_block, "toBlock": to_block, "address": contract.address, "topics": [transfer_event_signature]})

        transfers = []
        for log in logs:
            try:
                # Decode the event using the contract's ABI
                transfer_event = contract.events["Transfer(address,address,uint256)"]().process_log(log)
                from_address = transfer_event["args"]["from"]
                to_address = transfer_event["args"]["to"]
                value = transfer_event["args"]["value"]

                # Check if the transfer was facilitated by the contract
                if str(from_address).lower() != str(contract.address).lower() and str(to_address).lower() != str(contract.address).lower():
                    transfers.append(
                        {
                            "transactionHash": log["transactionHash"].hex(),
                            "blockHash": log["blockHash"].hex(),
                            "blockNumber": log["blockNumber"],
                            "logIndex": log["logIndex"],
                            "from": from_address,
                            "to": to_address,
                            "value": value,
                        }
                    )
            except Exception as e:
                # Log any errors during decoding
                transfers.append({"error": str(e), "transactionHash": log["transactionHash"].hex()})

        return transfers

    def print_transfer_event_details(self, event: Dict[str, Any], decimals: Decimal):
        """Print transfer event details."""
        click.echo("\nTransfer Event Details:")
        click.echo("--------------------------------------")
        if "error" in event:
            click.echo(f"Error decoding event: {event['error']} (Transaction: {event['transactionHash']})")
        else:
            from_address = event.get("from", "N/A")
            to_address = event.get("to", "N/A")
            value_raw = event.get("value", "N/A")
            transaction_hash = event.get("transactionHash", "N/A")

            # Format the value using the same approach as get_token_balance
            try:
                decimal_value = Decimal(value_raw) / Decimal(10**decimals)
                value = format(decimal_value, "f").rstrip("0").rstrip(".") or "0"
            except (ValueError, TypeError):
                value = "N/A"

            click.echo(f"Transaction Hash: {transaction_hash}")
            click.echo(f"From: {from_address}")
            click.echo(f"To: {to_address}")
            click.echo(f"Value: {value}")
            click.echo("--------------------------------------")

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

    def get_token_balance(self, wallet_address: str, contract: Contract, decimals: int) -> str:
        """Fetch the balance of a specific token for a given wallet address."""
        try:
            # Set the decimal context precision high enough to handle large numbers
            getcontext().prec = 50

            # Call the balanceOf function
            balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet_address)).call()

            # Convert balance and decimals to appropriate types
            balance_dec = Decimal(balance)
            decimals_dec = int(decimals)

            # Convert balance to human-readable format
            decimal_balance = balance_dec / (Decimal(10) ** decimals_dec)

            # Handle zero balance separately to avoid '0E-18' format
            if decimal_balance.is_zero():
                formatted_balance = "0"
            else:
                # Quantize to avoid scientific notation and set decimal places
                quantize_exponent = Decimal(f"1e-{decimals_dec}")
                decimal_balance = decimal_balance.quantize(quantize_exponent, rounding=ROUND_DOWN)

                # Convert to string
                formatted_balance = str(decimal_balance)

                # Remove trailing zeros and decimal point if necessary
                formatted_balance = formatted_balance.rstrip("0").rstrip(".")

                if not formatted_balance:
                    formatted_balance = "0"

            return formatted_balance

        except Exception as e:
            raise ValueError(f"Failed to fetch token balance: {str(e)}") from e

    def get_contract_swaps(self, contract: Contract, from_block: Optional[int] = None, to_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all Swap events facilitated by the contract."""
        if not self.w3.is_address(contract.address):
            raise ValueError("Invalid contract address")

        if from_block is None:
            latest = self.w3.eth.block_number
            from_block = max(0, latest - 1000)

        if to_block is None:
            to_block = self.w3.eth.block_number

        # Check if the Swap event is in the contract ABI
        if not hasattr(contract.events, "Swap"):
            return []  # Return an empty list if Swap event is not found

        # Get the Swap event from the contract
        swap_event = contract.events.Swap()

        # Fetch logs using the event filter
        logs = swap_event.get_logs(from_block=from_block, to_block=to_block)

        swaps = []
        for log in logs:
            try:
                # Fetch the number of decimals for the token
                decimals = self.get_token_decimals(contract)

                # Format the amounts using the decimals
                amount1In = Decimal(log.args.amount1In) / Decimal(10**decimals)
                amount0In = Decimal(log.args.amount0In) / Decimal(10**decimals)
                amount0Out = Decimal(log.args.amount0Out) / Decimal(10**decimals)
                amount1Out = Decimal(log.args.amount1Out) / Decimal(10**decimals)

                direction = "token0 to token1" if amount0In > 0 and amount1Out > 0 else "token1 to token0"
                swaps.append(
                    {
                        "transactionHash": log.transactionHash.hex(),
                        "blockHash": log.blockHash.hex(),
                        "blockNumber": log.blockNumber,
                        "logIndex": log.logIndex,
                        "sender": log.args.sender,
                        "to": log.args.to,
                        "amount1In": format(amount1In, "f").rstrip("0").rstrip(".") or "0",
                        "amount0In": format(amount0In, "f").rstrip("0").rstrip(".") or "0",
                        "amount0Out": format(amount0Out, "f").rstrip("0").rstrip(".") or "0",
                        "amount1Out": format(amount1Out, "f").rstrip("0").rstrip(".") or "0",
                        "direction": direction,
                        "changeInHoldings": {
                            "token0": f"-{amount0In}" if amount0In > 0 else f"+{amount0Out}",
                            "token1": f"-{amount1In}" if amount1In > 0 else f"+{amount1Out}",
                        },
                    }
                )
            except Exception as e:
                # Log any errors during decoding
                swaps.append({"error": str(e), "transactionHash": log.get("transactionHash", "N/A").hex()})

        return swaps

    def print_swap_event_details(self, event: Dict[str, Any], contract: Contract):
        """Print swap event details."""
        click.echo("\nSwap Event Details:")
        click.echo("--------------------------------------")
        if "error" in event:
            click.echo(f"Error decoding event: {event['error']} (Transaction: {event['transactionHash']})")
        else:
            sender = event.get("sender", "N/A")
            to = event.get("to", "N/A")
            amount0In = event.get("amount0In", "N/A")
            amount1In = event.get("amount1In", "N/A")
            amount0Out = event.get("amount0Out", "N/A")
            amount1Out = event.get("amount1Out", "N/A")
            transaction_hash = event.get("transactionHash", "N/A")
            direction = event.get("direction", "N/A")
            change_in_holdings = event.get("changeInHoldings", {})

            click.echo(f"Transaction Hash: {transaction_hash}")
            click.echo(f"Sender: {sender}")
            click.echo(f"To: {to}")
            click.echo(f"Amount0 In: {amount0In}")
            click.echo(f"Amount1 In: {amount1In}")
            click.echo(f"Amount0 Out: {amount0Out}")
            click.echo(f"Amount1 Out: {amount1Out}")
            click.echo(f"Direction: {direction}")
            click.echo(f"Change in Holdings: {change_in_holdings}")
        click.echo("--------------------------------------")
