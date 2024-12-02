#!/bin/zsh

# Check if .env already exists
if [ ! -f .env ]; then
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ".env file created. Please update it with your local configurations."
else
    echo ".env file already exists. Skipping copy."
fi