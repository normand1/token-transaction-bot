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

### Run Realtime Monitor
```
python -m src.cli monitor --contract-address 0x8a72f8c0184b825c724f0cc3d2229cc6c36ea9d7
```

### Run Playback Transaction for a Range of Blocks
```
python -m src.cli scan --contract-address 0x36a46dff597c5a444bbc521d26787f57867d2214 --from-block 23071608 --to-block 23071608
```