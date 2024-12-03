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

📝 Transaction: https://basescan.org/tx/daae9700c1c83b3b259e6afc18ba9bc146f1d1e382ec4892700aa3777e40b0ab
👤 Sender: https://basescan.org/address/0xE37e799D5077682FA0a244D46E5649F71457BD09
📮 Recipient: https://basescan.org/address/0x111111125421cA6dc452d289314280a0f8842A65
💱 PROXY: 9.126354092846732216 (PROXY)
💱 Wrapped Ether: -0.0196317 (Wrapped Ether)
↔️ Direction: BUY
--------------------------------------
```