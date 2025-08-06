# Discord Message Botter
Discord Message Botter is a Python script for Windows that sends messages from multiple accounts at regular intervals to a specific channel in a Discord server.

This script is made for botting Karuta drops + grabs, but can be easily repurposed for other uses.

## ⚠️ WARNING ⚠️
Discord's Terms of Service explicitly prohibits self-bots (as of June 2025). Unauthorized use of this script *could* result in account bans. Use at your own risk.

*In my experience, no accounts using this script have been banned by Discord, but I still recommend using throwaway accounts just to be safe.*

Note: This script extracts user tokens from Discord accounts using Selenium and Undetected-ChromeDriver. To keep your accounts safe, DO NOT share these tokens with anyone else and remember to close the script after use.

## Installation
1. Clone the repository.
2. Install Python 3.13.
3. Initialize a virtual environment, then install the required dependencies by running:
```bash
pip install -r requirements.txt
```
4. Ensure the Karuta drop mode is set to reactions, NOT buttons (`kdropmode`).
5. All accounts should ONLY drop 3 cards, not 4. If an accounts drops 4 cards, the fourth card will not be auto-grabbed.
6. Create/buy accounts for the script to use! I **highly recommend** purchasing FULLY VERIFIED alt accounts from a trusted shop. A fully verified account means that it has a verified email AND phone number- a phone number connected to the account is imperative because Discord frequently phone-locks suspicious accounts. (You don't need to have access to the phone, it just needs to be connected to your account.)

If you decide to buy accounts, I recommend purchasing from https://shop.xyliase.com/product/discord-accounts-%7C-fully-verified-tokens (I am not affiliated with this shop). As of July 2025, there is plenty of cheap stock and customer service is excellent.

> [!TIP]
> For the script to auto-grab all cards, the number of accounts you input must be a **multiple of 3**. Make sure no accounts have 2FA enabled, and all accounts should have message access in all of `self.COMMAND_CHANNEL_ID` and `self.DROP_CHANNEL_IDS`.

## Usage
1. Edit the `__init__` constants in `main.py`. `self.COMMAND_USER_IDS` restricts message commands to these accounts- leave the list empty if you want to allow *any* user to send commands. `self.COMMAND_CHANNEL_ID` is the channel where you can send message commands to control your accounts remotely. `self.DROP_CHANNEL_IDS` is a list of channels where the bot will drop cards. **There must be 1 drop channel per 3 accounts used.**
2. Enter your emails and passwords in `self.ACCOUNTS` in `token_extractor.py` using the following format:
```python
{"email": "example_email@gmail.com", "password": "example_password"}, ...
```

Alternatively, you can enter your tokens as a list of strings in `tokens.json`. **`tokens.json` MUST be in the root directory of the project (NOT in the message_botter folder).** Leave the list empty if you would like to use `self.ACCOUNTS` instead. 

**Generally, I recommend using tokens instead of account credentials so you can save time and avoid potential rate limiting.** If you don't have your tokens on hand, you can automatically extract and save your tokens to `tokens.json` by filling in your account credentials in `token_extractor.py`, setting `self.SAVE_TOKENS = True`, then running `main.py`.

3. If there is a special event going on in Karuta, you can set `self.SPECIAL_EVENT = True` in `main.py` AND enter a **single** token (a string) in `special_event_token.json` to automatically react to drops with the event emoji (if there is one). The token must, of course, have access to all `self.DROP_CHANNEL_IDS`. If there is no special event, you MUST set `self.SPECIAL_EVENT = False`.
4. Run `main.py`. It is **highly recommended** to run the program in a private channel to avoid interruptions. `self.COMMAND_USER_IDS` prevents other people from using message commands, but you can also set `self.COMMAND_SERVER_ID` and `self.COMMAND_CHANNEL_ID` to an empty string to disable message commands.
5. To send a message from any account, manually send a message in the `self.COMMAND_CHANNEL_ID` channel using the following format (without angle brackets):
```bash
cmd <account_number |OR| 'all'> <message>
```
- Ex 1. `cmd all kcollection o:wishlist` sends `kcollection o:wishlist` from ALL accounts.
- Ex 2. `cmd 1 kgive @ExxML <card_code>` sends a card transfer from Account #1 (the first account listed in `self.ACCOUNTS`). A few seconds after the transfer is sent, the script will automatically confirm the transfer (from Account #1).
- Ex 3. `cmd 3 kmultitrade @ExxML` sends a multitrade request from Account #3. After the trade items have been entered, type `cmd 3 /lock` to lock and confirm the trade (from Account #3).
- Ex 4. `cmd 1 kmultiburn <filters>` multiburns cards on Account #1. When you are FULLY READY to complete the multiburn, type `cmd 1 /burn` to confirm the multiburn.
- Ex 5. `cmd 1 /b <emoji / label>` clicks the button with the specified emoji OR label from Account #1. For example, `cmd 1 /b ✅` or `cmd 1 /b Confirm`.
- Ex 6. `cmd /pause` / `cmd /resume` pauses and resumes the script.

> [!NOTE]
> - The `all` argument does not work with `give`, `multitrade`, `/lock`, `multiburn`, or `/burn` commands.
> - If you mistype the account number for the `/lock` or `/burn` command, you must restart the trade/burn process. Sorry!
> - Automatic confirmation for the `kburn` command will not be supported. Use `kmultiburn` instead.

#### ⚠️ **DO NOT** run the script for more than 10 consecutive hours. Karuta may flag your accounts for suspicious activity. After a random time limit, the script will automatically stop and display a warning in the terminal.
#### ⚠️ **DO NOT** run this script too many times in a row because you will get login rate-limited by Discord Web. The cooldown after being rate-limited is typically a few hours.

## Top.gg Auto-Voter
### Usage
1. Follow the usage steps above (for Discord Message Botter) to obtain a list of tokens in `tokens.json`.
2. Ensure your (normal) Chrome browser is up-to-date.
3. **DO NOT** use a VPN while running this script. Cloudflare flags VPNs.
4. If you wish, edit `self.RAND_DELAY_MIN` and `self.RAND_DELAY_MAX` to change the (randomized) amount of time between votes.
5. Run `auto_voter.py`.