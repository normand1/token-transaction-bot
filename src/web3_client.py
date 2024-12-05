"""Web3 client for interacting with Base L2."""

import os
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

import click
from dotenv import load_dotenv
from web3 import Web3
from web3.contract import Contract

from src.basescan_client import BaseScanClient

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

    def get_contract_swaps(self, contract: Contract, from_block: Optional[int] = None, to_block: Optional[int] = None, dry_run: bool = False) -> List[Dict[str, Any]]:
        """Get all Swap events facilitated by the contract. This is used for realtime monitoring and historical analysis.

        Args:
            contract (Contract): The Web3 contract instance to query events from.
            from_block (Optional[int]): Starting block number for the event query. Defaults to (latest - 1000) if None.
            to_block (Optional[int]): Ending block number for the event query. Defaults to latest block if None.
            dry_run (bool): If True, adds dry run flag to swap events. Defaults to False.

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
            raise RuntimeError(f"Error initializing token contracts: {str(e)}") from e

        # Get the Swap event logs
        swap_event = contract.events.Swap()
        try:
            click.echo(f"Fetching Swap event logs from block {from_block} to {to_block}")
            logs = swap_event.get_logs(from_block=from_block, to_block=to_block)
        except Exception as e:
            raise RuntimeError(f"Error fetching Swap event logs: {str(e)}") from e

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
                        "transactionHash": "0x" + log.transactionHash.hex(),
                        "blockHash": "0x" + log.blockHash.hex(),
                        "blockNumber": log.blockNumber,
                        "logIndex": log.logIndex,
                        "sender": getattr(args, "sender", None) or "N/A",
                        "recipient": getattr(args, "recipient", None) or "N/A",
                        "dry_run": dry_run,
                    }
                )

                swaps.append(swap_data)

            except Exception as e:
                swaps.append(
                    {
                        "error": str(e),
                        "transactionHash": "0x" + log.transactionHash.hex() if hasattr(log, "transactionHash") else "N/A",
                    }
                )

        return swaps
