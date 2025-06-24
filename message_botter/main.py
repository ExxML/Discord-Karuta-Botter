from token_getter import TokenGetter
from datetime import datetime
import win32gui
import win32con
import win32console
import aiohttp
import asyncio
import base64
import json
import random
import sys
import ctypes
import uuid

# Customize these settings
TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
SERVER_ID = ""  # Enter your target server
CHANNEL_ID = ""  # Enter your target channel
KARUTA_PREFIX = "k"  # Karuta's bot prefix
MESSAGE_COMMAND_TOGGLE = True

MESSAGE_COMMAND_PREFIX = "{cmd}"
ALL_ACCOUNT_FLAG = "all"
KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID
KARUTA_DROP_MESSAGE = "is dropping 3 cards!"
KARUTA_EXPIRED_DROP_MESSAGE = "This drop has expired and the cards can no longer be grabbed."
KARUTA_CARD_TRANSFER_MESSAGE = "Card Transfer"
RATE_LIMIT = 3  # Maximum number of rate limits before giving up
EMOJI_MAP = {
    '1️⃣': '[1]',
    '2️⃣': '[2]',
    '3️⃣': '[3]'
}

# Construct realistic Discord browser headers
token_headers = {}
def get_headers(token: str):
    if token not in token_headers:
        chrome_version = random.choice(["126.0.6478.127", "127.0.6533.89", "128.0.6613.85"])  # Recent chrome versions (June 2025)
        build_number = random.choice([298123, 301456, 305789])  # Recent Discord build numbers (June 2025)
        super_properties = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "system_locale": "en-US",
            "browser_user_agent": (
                f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                f"AppleWebKit/537.36 (KHTML, like Gecko) "
                f"Chrome/{chrome_version} Safari/537.36"
            ),
            "browser_version": chrome_version,
            "os_version": "10",
            "referrer": "https://discord.com/channels/@me",
            "referring_domain": "discord.com",
            "referrer_current": "https://discord.com/channels/@me",
            "referring_domain_current": "discord.com",
            "release_channel": "stable",
            "client_build_number": build_number,
            "client_event_source": None
        }
        x_super_props = base64.b64encode(
            json.dumps(super_properties, separators=(',', ':')).encode()
        ).decode()

        token_headers[token] = {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": super_properties["browser_user_agent"],
            "X-Super-Properties": x_super_props,
            "X-Discord-Locale": "en-US",
            "X-Debug-Options": "bugReporterEnabled",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
            "X-Context-Properties": base64.b64encode(json.dumps({
                "location": "Channel",
                "location_guild_id": SERVER_ID,
                "location_channel_id": CHANNEL_ID,
                "location_channel_type": 1,
            }).encode()).decode()
        }
    return token_headers[token]

async def check_command(token: str):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=10"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                messages = await resp.json()
                for msg in messages:
                    try:
                        msg_id = msg.get('id')
                        raw_content = msg.get('content', '')
                        if raw_content.startswith(MESSAGE_COMMAND_PREFIX) and msg_id not in executed_commands:
                            executed_commands.append(msg_id)
                            content = raw_content.removeprefix(MESSAGE_COMMAND_PREFIX).strip()
                            account_str, command = content.split(" ", 1)
                            if account_str.isdigit():
                                account = int(account_str)
                                if account < 1 or account > len(tokens):
                                    print(f"❌ Error parsing command: Account number is not between 1 and {len(tokens)}.")
                                    return None, None
                            elif account_str.lower() == ALL_ACCOUNT_FLAG:
                                account = ALL_ACCOUNT_FLAG
                            else:
                                print(f"❌ Error parsing command: Account number is not a number or 'all'.")
                                return None, None
                            print(f"🤖 Sending '{command}' from {f"Account #{account}" if isinstance(account, int) else "all accounts"}...")
                            return account, command
                    except Exception as e:
                        print("❌ Error parsing command:", e)
                        return None, None
            else:
                print(f"❌ Command check failed: Error code {status}.")
                return None, None
            # If status = 200 but no MESSAGE_COMMAND_PREFIX found
            return None, None

async def check_give_card(token:str, account: int, command: str):
    raw_command = command.removeprefix(KARUTA_PREFIX).strip()
    if raw_command.startswith("g") or raw_command.startswith("give"):
        await asyncio.sleep(random.uniform(5, 8))  # Wait for Karuta card transfer message
        card_transfer_message = await get_karuta_message(token, account, KARUTA_CARD_TRANSFER_MESSAGE, RATE_LIMIT)
        if card_transfer_message:
            msg_id = card_transfer_message.get('id')
            if msg_id not in executed_card_transfers:
                executed_card_transfers.append(msg_id)
                # Find ✅ check button
                components = card_transfer_message.get('components', [])
                for action_row in components:
                    for button in action_row.get('components', []):
                        if button.get('emoji', {}).get('name') == '✅':
                            custom_id = button.get('custom_id')
                            # Simulate button click via interaction callback
                            interaction_url = "https://discord.com/api/v10/interactions"
                            payload = {
                                "type": 3,  # Component interaction
                                "nonce": str(uuid.uuid4().int >> 64),  # Unique interaction ID
                                "guild_id": SERVER_ID,
                                "channel_id": CHANNEL_ID,
                                "message_flags": 0,
                                "message_id": card_transfer_message.get('id'),
                                "application_id": KARUTA_BOT_ID,
                                "session_id": str(uuid.uuid4()),
                                "data": {
                                    "component_type": 2,
                                    "custom_id": custom_id
                                }
                            }
                            async with aiohttp.ClientSession() as session:
                                headers = get_headers(token)
                                async with session.post(interaction_url, headers = headers, json = payload) as button_resp:
                                    status = button_resp.status
                                    if status == 204:
                                        print(f"✅ [Account #{account}] Clicked check button successfully.")
                                    else:
                                        print(f"❌ [Account #{account}] Click check button failed: Error code {status}.")
                                return
                    print(f"❌ [Account #{account}] Click check button failed: Check button not found.")

async def message_command():
    while True:
        account, command = await check_command(random.choice(tokens))  # Use a random account to check for message commands
        if account == ALL_ACCOUNT_FLAG and command:
            for index, token in enumerate(tokens):
                account = index + 1
                await send_message(token, account, command, RATE_LIMIT)  # Won't retry even if rate-limited (so it doesn't interfere with drops/grabs)
                await check_give_card(token, account, command)
                await asyncio.sleep(random.uniform(1, 3))
            print("🤖 Message command executed.")
        elif account and command:
            await send_message(tokens[account - 1], account, command, RATE_LIMIT)
            await check_give_card(tokens[account - 1], account, command)
            print("🤖 Message command executed.")
        await asyncio.sleep(random.uniform(2, 5))  # Short delay to avoid getting rate-limited

async def send_message(token: str, account: int, content: str, rate_limited: int):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = get_headers(token)
    payload = {
        "content": content,
        "tts": False,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers = headers, json = payload) as resp:
            status = resp.status
            if status == 200:
                print(f"✅ [Account #{account}] Sent message '{content}'.")
            elif status == 401:
                print(f"❌ [Account #{account}] Message '{content}' failed: Invalid token.")
            elif status == 403:
                print(f"❌ [Account #{account}] Message '{content}' failed: Token banned or no permission.")
            elif status == 429 and rate_limited < RATE_LIMIT:
                rate_limited += 1
                retry_after = 2  # seconds
                print(f"⚠️ [Account #{account}] Message '{content}' failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await send_message(token, account, content, rate_limited)  # Retry drop
            else:
                print(f"❌ [Account #{account}] Message '{content}' failed: Error code {status}.")
            return status == 200

async def get_karuta_message(token: str, account: int, search_content: str, rate_limited: int):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=10"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                messages = await resp.json()
                for msg in messages:
                    if msg.get('author', {}).get('id') == KARUTA_BOT_ID:
                        if search_content == KARUTA_DROP_MESSAGE in msg.get('content', '') and KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', ''):
                                print(f"✅ [Account #{account}] Retrieved drop message.")
                                return msg 
                        elif search_content == KARUTA_CARD_TRANSFER_MESSAGE == msg['embeds'][0].get('title'):
                                print(f"✅ [Account #{account}] Retrieved card transfer message.")
                                return msg
            elif status == 429 and rate_limited < RATE_LIMIT:
                rate_limited += 1
                retry_after = 2  # seconds
                print(f"⚠️ [Account #{account}] Retrieve message failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                return await get_karuta_message(token, account, search_content, rate_limited)  # Retry getting message
            else:
                print(f"❌ [Account #{account}] Retrieve message failed: Error code {status}.")
                return None
            # If status = 200 but no drop found
            print(f"❌ [Account #{account}] Retrieve message failed: Message '{search_content}' not found in recent messages.")
            return None

async def add_reaction(token: str, account: int, message_id: str, emoji: str, rate_limited: int):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{message_id}/reactions/{emoji}/@me"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers = headers) as resp:
            status = resp.status
            card_number = EMOJI_MAP.get(emoji)
            if status == 204:
                print(f"✅ [Account #{account}] Grabbed card {card_number}.")
            elif status == 401:
                print(f"❌ [Account #{account}] Grab card {card_number} failed: Invalid token.")
            elif status == 403:
                print(f"❌ [Account #{account}] Grab card {card_number} failed: Token banned or no permission.")
            elif status == 429 and rate_limited < RATE_LIMIT:
                rate_limited += 1
                retry_after = 2  # seconds
                print(f"⚠️ [Account #{account}] Grab card {card_number} failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await add_reaction(token, account, message_id, emoji, rate_limited)  # Retry reaction
            else:
                print(f"❌ [Account #{account}] Grab card {card_number} failed: Error code {status}.")

async def main():
    if MESSAGE_COMMAND_TOGGLE:
        # Launch the command message checker as a background task
        asyncio.create_task(message_command())
        print("\n🤖 Message commands enabled.")
    else:
        print("\n🤖 Message commands disabled.")

    account_num = len(tokens)
    if account_num == 0:
        input("⛔ Token Error ⛔\nNo tokens found. Please check your account info.")
        sys.exit()
    delay = 30 * 60 / account_num  # Karuta drop cooldown is 30 mins- set delay to spread out drops
    if account_num < 3:
        grab_pointer = 0  # Token pointer for auto-grab
    else:
        grab_pointer = account_num - 3
    random_addon = ['', ' ', ' !', ' :D', ' w']  # Variance to avoid detection
    drop_messages = [f"{KARUTA_PREFIX}drop", f"{KARUTA_PREFIX}d"]
    random_messages = [
        f"{KARUTA_PREFIX}reminders", 
        f"{KARUTA_PREFIX}rm",
        f"{KARUTA_PREFIX}lookup",
        f"{KARUTA_PREFIX}lu",
        f"{KARUTA_PREFIX}vote",
        f"{KARUTA_PREFIX}view",
        f"{KARUTA_PREFIX}v",
        f"{KARUTA_PREFIX}collection",
        f"{KARUTA_PREFIX}c",
        f"{KARUTA_PREFIX}cardinfo",
        f"{KARUTA_PREFIX}ci",
        f"{KARUTA_PREFIX}cd"
    ]
    emojis = ['1️⃣', '2️⃣', '3️⃣']
    
    while True:
        for index, token in enumerate(tokens):
            print(f"\n{datetime.now().strftime("%I:%M:%S %p").lstrip("0")}")  # Timestamp
            account = index + 1
            drop_message = random.choice(drop_messages) + random.choice(random_addon)  # Randomize message
            sent = await send_message(token, account, drop_message, 0)
            if sent:
                await asyncio.sleep(random.uniform(5, 8))  # Wait for drop message to fully load
                karuta_message = await get_karuta_message(token, account, KARUTA_DROP_MESSAGE, 0)
                if karuta_message:
                    karuta_message_id = karuta_message.get('id')
                    random.shuffle(emojis)
                    for i in range(0, 3):
                        emoji = emojis[i]
                        grab_index = (grab_pointer + i) % account_num
                        grab_token = tokens[grab_index]
                        grab_account = grab_index + 1
                        await add_reaction(grab_token, grab_account, karuta_message_id, emoji, 0)
                        await asyncio.sleep(random.uniform(0, 1))
                        random_message = random.choice(random_messages)
                        await send_message(grab_token, grab_account, random_message, RATE_LIMIT)  # Won't retry even if rate-limited
            else:
                # Set terminal window on top to notify user of invalid token
                if TERMINAL_VISIBILITY:
                    hwnd = win32console.GetConsoleWindow()
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(hwnd)
                    input("⛔ Request Error ⛔\nMalformed request. Possible causes include:\n 1. Invalid/expired token\n 2. Incorrectly inputted server/channel/bot ID\nPress `Enter` to restart the script.")
                    ctypes.windll.shell32.ShellExecuteW(
                        None, None, sys.executable, " ".join(sys.argv), None, TERMINAL_VISIBILITY
                    )
                sys.exit()
            grab_pointer = (grab_pointer + 3) % account_num  # Move pointer to next account (3 accounts per drop)
            await asyncio.sleep(delay + random.uniform(0, 40))  # Additional random delay between drops

if __name__ == "__main__":
    # Flag to check if script relaunched
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, TERMINAL_VISIBILITY
        )
        sys.exit()
    if len(SERVER_ID) == 0 or len(CHANNEL_ID) == 0 or len(KARUTA_BOT_ID) == 0:
        input("⛔ Configuration Error ⛔\nPlease use a valid server ID, channel ID, and Karuta bot ID in `main.py`.")
        sys.exit()
    tokens = TokenGetter().main()
    executed_commands = []
    executed_card_transfers = []
    asyncio.run(main())