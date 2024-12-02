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

## Example output

### Swap Events
```
Swap Event Details:
--------------------------------------
Transaction Hash: bb8a868cfdb4d41a1c1d2c426fc216ffd8a8bcd524c1e3427f0d9701145f34f1
Sender: 0xE37e799D5077682FA0a244D46E5649F71457BD09
To: 0x1111111254EEB25477B68fb85Ed929f73A960582
Amount0 In: 0.133521502759972748
Amount1 In: 0
Amount0 Out: 0
Amount1 Out: 0.000004494317262057
Direction: token0 to token1
Change in Holdings: {'token0': '-0.133521502759972748', 'token1': '+0.000004494317262057'}
--------------------------------------
```

### Transfer Events
```
Transfer Event Details:
--------------------------------------
Transaction Hash: 530d55e0d8749309dff54f03508f54bfed7f4d410338bc7d77bbfd74ab23b3ca
From: 0x0B6De7c23281Af24A542C127e96864247983Dea4
To: 0x509dE3bd5eCe4a8d61C2b82aFDeEBc3f41A99A18
Value: 185.875827271336738996
--------------------------------------
```