"""Command line interface for the Token Transaction Bot."""

import click
import time
from .web3_client import Web3Client
from .basescan_client import BaseScanClient
from web3 import Web3


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Token Transaction Bot - Manage and monitor token transactions on Base L2."""


@cli.command()
@click.option(
    "--contract-address",
    required=True,
    help="The contract address to monitor",
)
@click.option(
    "--poll-interval",
    default=12,
    help="Polling interval in seconds (default: 12)",
    type=int,
)
def monitor(contract_address: str, poll_interval: int):
    """Monitor transactions for a specific contract on Base L2."""
    client = Web3Client()
    basescan_client = BaseScanClient()

    if not client.is_connected():
        click.echo("Error: Could not connect to Base L2")
        return

    # Load the contract ABI
    try:
        click.echo(f"Loading contract ABI for {contract_address}")
        checksum_address = Web3.to_checksum_address(contract_address)
        contract = basescan_client.load_contract(checksum_address)
    except ValueError as e:
        click.echo(f"Error loading contract ABI: {e}")
        return

    click.echo("Connected to Base L2")
    click.echo(f"Monitoring pool ca: {contract_address}")
    click.echo(f"Latest block: {client.get_latest_block()}")
    click.echo("Waiting for new events...")

    last_block = client.get_latest_block()

    try:
        while True:
            current_block = client.get_latest_block()
            if current_block > last_block:
                swap_events = client.get_contract_swaps(contract, from_block=last_block + 1, to_block=current_block)
                click.echo(f"Found {len(swap_events)} new swap events")

                for swap_event in swap_events:
                    client.print_swap_event_details(swap_event)

                last_block = current_block
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        click.echo("\nStopping monitor...")


@cli.command()
@click.option(
    "--contract-address",
    required=True,
    help="The contract address to scan",
)
@click.option(
    "--from-block",
    default=None,
    help="Start block number (default: last 1000 blocks)",
    type=int,
)
@click.option(
    "--to-block",
    default=None,
    help="End block number (default: latest)",
    type=int,
)
def scan(contract_address: str, from_block: int, to_block: int):
    """Scan the blockchain for contract events."""
    client = Web3Client()
    basescan_client = BaseScanClient()
    if not client.is_connected():
        click.echo("Error: Could not connect to Base L2")
        return

    # Load the contract ABI
    try:
        click.echo(f"Loading contract ABI for {contract_address}")
        checksum_address = Web3.to_checksum_address(contract_address)
        contract = basescan_client.load_contract(checksum_address)
    except ValueError as e:
        click.echo(f"Error loading contract ABI: {e}")
        return

    click.echo("Connected to Base L2")
    click.echo(f"Scanning contract: {contract.address}")

    try:
        swap_events = client.get_contract_swaps(contract, from_block=from_block, to_block=to_block)
        click.echo(f"Found {len(swap_events)} new swap events")

        for swap_event in swap_events:
            client.print_swap_event_details(swap_event)

    except ValueError as e:
        click.echo(f"Error: {str(e)}")


if __name__ == "__main__":
    cli()
