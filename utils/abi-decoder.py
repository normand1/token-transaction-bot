"""
Utility to decode ABI and print function selectors for debugging purposes only.
"""

import json
from eth_utils import keccak
import argparse


def get_function_selectors(abi):
    selectors = {}
    for item in abi:
        if item["type"] == "function":
            # Build the function signature
            signature = f"{item['name']}({','.join(i['type'] for i in item['inputs'])})"
            # Compute the selector
            selector = keccak(text=signature).hex()[:10]
            selectors[selector] = signature
    return selectors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Decode ABI and print function selectors")
    parser.add_argument("--abi-file", type=str, default="proxy-abi.json", help="path to the ABI JSON file")

    args = parser.parse_args()

    # Load ABI from file
    with open(args.abi_file, "r") as f:
        abi = json.load(f)

    selectors = get_function_selectors(abi)
    print(selectors)
