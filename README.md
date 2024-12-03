# Token Transaction Bot

## Setup

1. Ensure you have pyenv installed
2. Set up the Python environment:
```bash
pyenv local 3.12.1
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install pip-tools
pip-compile requirements.in
pip install -r requirements.txt
```

## Development

- Source code is in the `src` directory
- Tests are in the `tests` directory

## Running Tests

```bash
pytest tests/
``` 

## Running the token transaction bot

Before running the first time run the following script to setup the .env file:
```bash
./setup.sh
```

## Secrets / API Keys

The only secret required to run this app is a free API Key from https://basescan.org/
Once you have acquired one you can update it in the .env file


### Run Realtime Monitor
```
python -m src.cli monitor --contract-address 0xeD6f2a73b85e61bD1FB68A8bAaA1b0Dc91B717C6
```

### Run Playback Transaction for a Range of Blocks
```
python -m src.cli scan --contract-address 0xeD6f2a73b85e61bD1FB68A8bAaA1b0Dc91B717C6 --from-block 23071608 --to-block 23071608
```

## Example output

### Swap Events
```
Swap Event Details:
--------------------------------------
🔄 New Swap Event

📝 Transaction: https://basescan.org/tx/3b0afab80d027f9ccce1b240536891fd8484f425509f901aa68025b89055ab58
👤 Sender: https://basescan.org/address/0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD
📮 Recipient: https://basescan.org/address/0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD
💱 PROXY: -415.699558092902942699 (PROXY)
💱 Wrapped Ether: 0.8 (Wrapped Ether)
↔️ Direction: BUY
--------------------------------------
```