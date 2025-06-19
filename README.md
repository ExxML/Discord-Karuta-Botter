# Discord Message Botter
Discord Message Botter is a Python script for Windows that sends messages from multiple accounts at regular intervals to a specific channel in a Discord server.

This script is made for botting Karuta drops + grabs, but can be easily repurposed for other uses.

## ⚠️ WARNING ⚠️
Discord's Terms of Service explicitly prohibits self-bots (as of June 2025). Unauthorized use of this script *could* result in account bans. Use at your own risk.

*In my experience, no accounts using this script have been banned, but I still recommend using throwaway accounts just to be safe.*

Note: This script extracts user tokens from Discord accounts using Selenium and Undetected-ChromeDriver. To keep your accounts safe, DO NOT share these tokens with anyone else and remember to close the script after use.

## Installation
1. Install Python 3.13.
2. Initialize a virtual environment and install the required dependencies by running:
```bash
pip install -r requirements.txt
```

## Usage
1. Edit `SERVER_ID` and `CHANNEL_ID` in `main.py` to match your target server and channel.
2. Edit `ACCOUNTS` in `token_getter.py` to match your account emails and passwords. To successfully grab all cards dropped, you must enter at least 3 accounts. Make sure all accounts have message access to the target server and channel. 
3. Run `main.py`.
- ⚠️ Note: **DO NOT** run this script too many times in a row because you will get rate-limited by Discord Web. The cooldown after being rate-limited is typically a few hours.