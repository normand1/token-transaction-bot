#!/bin/zsh
while true; do
  python -m src.cli monitor --contract-address 0xeD6f2a73b85e61bD1FB68A8bAaA1b0Dc91B717C6 >> logfile.log 2>&1
  echo "Command crashed with exit code $?. Restarting..." >> logfile.log
  sleep 5  # Prevent rapid restart in case of repeated failures
done