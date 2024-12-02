import os
import requests
import json
from typing import List, Dict, Any
from decimal import Decimal
from web3 import Web3
from web3.contract import Contract
from web3.types import ChecksumAddress
import click


class BaseScanClient:
    """Client for interacting with BaseScan API to fetch contract data."""

    contract_address: str
    contract_abi: List[Dict[str, Any]]

    def __init__(self):
        self.api_key = os.getenv("BASESCAN_API_KEY")
        self.url = os.getenv("BASE_SCAN_URL") + "/api"
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("BASE_RPC_URL")))

    def fetch_contract_abi(self, address: str) -> List[Dict[str, Any]]:
        """Fetch ABI dynamically from BaseScan."""
        api_key = os.getenv("BASESCAN_API_KEY")
        url = os.getenv("BASE_SCAN_URL") + "/api"

        params = {
            "module": "contract",
            "action": "getabi",
            "address": address,
            "apikey": api_key,
        }

        try:
            # Make the API call
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            if data["status"] == "1":
                # Return the parsed ABI
                return json.loads(data["result"])
            else:
                # Handle error response from BaseScan
                raise ValueError(f"BaseScan API error: {data.get('result', 'Unknown error')}")

        except requests.RequestException as e:
            raise ValueError(f"Failed to fetch ABI from BaseScan: {e}") from e

    def load_contract(self, address: ChecksumAddress) -> Contract:
        """Load a contract's ABI and create a contract instance."""
        self.contract_address = address
        try:
            self.contract_abi = self.fetch_contract_abi(address)
            if not self.contract_abi:
                raise ValueError("ABI is empty. Ensure the contract is verified or provide a local ABI.")
        except Exception as e:
            raise ValueError(f"Failed to fetch ABI for contract {address}: {e}") from e

        return self.w3.eth.contract(address=address, abi=self.contract_abi)

    def get_token_balance(self, address: str, contract: Contract, decimals: Decimal, block_identifier: int = "latest") -> Decimal:
        """Fetch token balance for a given address at a specific block."""
        try:
            balance_raw = contract.functions.balanceOf(address).call(block_identifier=block_identifier)
            return Decimal(balance_raw) / Decimal(10**decimals)
        except Exception as e:
            raise ValueError(f"Error fetching balance for address {address}: {e}")
