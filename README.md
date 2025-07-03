# Discord Message Botter
Discord Message Botter is a Python script for Windows that sends messages from multiple accounts at regular intervals to a specific channel in a Discord server.

This script is made for botting Karuta drops + grabs, but can be easily repurposed for other uses.

## ⚠️ WARNING ⚠️
Discord's Terms of Service explicitly prohibits self-bots (as of June 2025). Unauthorized use of this script *could* result in account bans. Use at your own risk.

*In my experience, no accounts using this script have been banned, but I still recommend using throwaway accounts just to be safe.*

Note: This script extracts user tokens from Discord accounts using Selenium and Undetected-ChromeDriver. To keep your accounts safe, DO NOT share these tokens with anyone else and remember to close the script after use.

## Installation
1. Clone the repository.
2. Install Python 3.13.
3. Initialize a virtual environment, then install the required dependencies by running:
```bash
pip install -r requirements.txt
```

## Usage
1. Edit `CHANNEL_ID` and `KARUTA_PREFIX` in `main.py` to match your target channel and Karuta bot prefix.
2. Edit `ACCOUNTS` in `token_getter.py` to match your account emails and passwords. **To successfully grab all cards dropped, the number of accounts you enter must be a multiple of 3.** Make sure all accounts have message access to the target server and channel. 
3. Run `main.py`. It is **highly** recommended to run the program in a private channel to avoid interruptions. If you choose to run the program in a public channel, turn off `MESSAGE_COMMAND_TOGGLE` in `main.py` to prevent other users controlling your accounts.
4. To send a message from any account, manually send a message in the target channel with the following format (without angle brackets):
```bash
{cmd} <account_number |OR| 'all'> <message>
```
- Ex 1. `{cmd} all kcollection o:wishlist` sends `kcollection o:wishlist` from ALL accounts.
- Ex 2. `{cmd} 1 kgive @ExxML <card_code>` sends a card transfer from Account #1 (of `ACCOUNTS` in `token_getter.py`). A few seconds after the transfer is sent, the script will automatically confirm the transfer (from Account #1).
- Ex 3. `{cmd} 3 kmultitrade @ExxML` sends a multitrade request from Account #3. After the trade items have been entered, type `{cmd} 3 {lock}` to lock and confirm the trade (from Account #3).
- Ex 4. `{cmd} 1 kmultiburn <filter>` multiburns cards on Account #1. When you are FULLY READY to complete the multiburn, type `{cmd} 1 {burn}` to confirm the multiburn. 
- Ex 5. `{cmd} play` / `{cmd} pause` plays/pauses all drops. When paused, message commands are still processed.

##### Note #1: The `all` argument does not work with `give`, `multitrade`, `{lock}`, `multiburn`, or `{multiburn}` commands.
##### Note #2: If you mistype the account number for the `{lock}` or `{multiburn}` command, you must restart the trade/burn process. Sorry!
##### Note #3: Automatic confirmation for the `kburn` command will not be supported. Use `kmultiburn` instead.

#### ⚠️ **DO NOT** run this script too many times in a row because you will get login rate-limited by Discord Web. The cooldown after being rate-limited is typically a few hours.