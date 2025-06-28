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
INTERACTION_URL = "https://discord.com/api/v10/interactions"

KARUTA_DROP_MESSAGE = "is dropping 3 cards!"
KARUTA_EXPIRED_DROP_MESSAGE = "This drop has expired and the cards can no longer be grabbed."

KARUTA_CARD_TRANSFER_TITLE = "Card Transfer"

KARUTA_MULTITRADE_LOCK_MESSAGE = "Both sides must lock in before proceeding to the next step."
KARUTA_MULTITRADE_CONFIRM_MESSAGE = "This trade has been locked."
KARUTA_LOCK_COMMAND = "{lock}"

KARUTA_MULTIBURN_TITLE = "Burn Cards"
KARUTA_MULTIBURN_COMMAND = "{multiburn}"

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
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=3"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                messages = await resp.json()
                for msg in messages:
                    try:
                        raw_content = msg.get('content', '')
                        if raw_content.startswith(MESSAGE_COMMAND_PREFIX) and msg not in executed_commands:
                            executed_commands.append(msg)
                            content = raw_content.removeprefix(MESSAGE_COMMAND_PREFIX).strip()
                            account_str, command = content.split(" ", 1)
                            if account_str.isdigit():
                                account = int(account_str)
                                if account < 1 or account > len(tokens):
                                    print(f"❌ Error parsing command: Account number is not between 1 and {len(tokens)}.")
                                    return None, None, None
                            elif account_str.lower() == ALL_ACCOUNT_FLAG:
                                account = ALL_ACCOUNT_FLAG
                            else:
                                print(f"❌ Error parsing command: Account number is not a number or 'all'.")
                                return None, None, None
                            if (command.startswith(f"{KARUTA_PREFIX}give") or command.startswith(f"{KARUTA_PREFIX}g")) and isinstance(account, int):
                                print(f"🤖 Sending card transfer from Account #{account}...")
                                send = True
                            elif command == KARUTA_LOCK_COMMAND and isinstance(account, int):
                                print(f"🤖 Locking and confirming trade from Account #{account}...")
                                send = False
                            elif (command.startswith(f"{KARUTA_PREFIX}multiburn") or command.startswith(f"{KARUTA_PREFIX}mb")) and isinstance(account, int):
                                print(f"🤖 Multiburning on Account #{account}...")
                                send = True
                            elif command == KARUTA_MULTIBURN_COMMAND and isinstance(account, int):
                                print(f"🤖 Confirming multiburn on Account #{account}...")
                                send = False
                            else:
                                print(f"🤖 Sending '{command}' from {f"Account #{account}" if isinstance(account, int) else "all accounts"}...")
                                send = True
                            return send, account, command
                    except Exception as e:
                        print("❌ Error parsing command:", e)
                        return None, None, None
            else:
                print(f"❌ Command check failed: Error code {status}.")
                return None, None, None
            # If status = 200 but no MESSAGE_COMMAND_PREFIX found
            return None, None, None

async def find_button(account: int, emoji: str, message: dict):
    try:
        components = message.get('components', [])
        for action_row in components:
            for button in action_row.get('components', []):
                if button.get('emoji', {}).get('name') == emoji:
                    custom_id = button.get('custom_id')
                    # Simulate button click via interaction callback
                    payload = {
                        "type": 3,  # Component interaction
                        "nonce": str(uuid.uuid4().int >> 64),  # Unique interaction ID
                        "guild_id": SERVER_ID,
                        "channel_id": CHANNEL_ID,
                        "message_flags": 0,
                        "message_id": message.get('id'),
                        "application_id": KARUTA_BOT_ID,
                        "session_id": str(uuid.uuid4()),
                        "data": {
                            "component_type": 2,
                            "custom_id": custom_id
                        }
                    }
                    print(f"✅ [Account #{account}] Found {emoji} button successfully.")
                    return payload
    except Exception as e:
        print(f"❌ [Account #{account}] Interaction failed: {emoji} button not found.")
        return None

async def check_card_transfer(token: str, account: int, command: str):
    if command.startswith(f"{KARUTA_PREFIX}give") or command.startswith(f"{KARUTA_PREFIX}g"):
        await asyncio.sleep(random.uniform(4, 6))  # Wait for Karuta card transfer message
        card_transfer_message = await get_karuta_message(token, account, KARUTA_CARD_TRANSFER_TITLE, RATE_LIMIT)
        if card_transfer_message and card_transfer_message not in card_transfer_messages:
            card_transfer_messages.append(card_transfer_message)
            # Find ✅ button
            payload = await find_button(account, '✅', card_transfer_message)
            if payload is not None:
                async with aiohttp.ClientSession() as session:
                    headers = get_headers(token)
                    async with session.post(INTERACTION_URL, headers = headers, json = payload) as resp:
                        status = resp.status
                        if status == 204:
                            print(f"✅ [Account #{account}] Confirmed card transfer.")
                        else:
                            print(f"❌ [Account #{account}] Confirm card transfer failed: Error code {status}.")

async def check_multitrade(token: str, account: int, command: str):
    if command == KARUTA_LOCK_COMMAND:
        multitrade_lock_message = await get_karuta_message(token, account, KARUTA_MULTITRADE_LOCK_MESSAGE, RATE_LIMIT)
        if multitrade_lock_message and multitrade_lock_message not in multitrade_messages:
            multitrade_messages.append(multitrade_lock_message)
            # Find 🔒 button
            lock_payload = await find_button(account, '🔒', multitrade_lock_message)
            if lock_payload is not None:
                async with aiohttp.ClientSession() as session:
                    headers = get_headers(token)
                    async with session.post(INTERACTION_URL, headers = headers, json = lock_payload) as lock_resp:
                        status = lock_resp.status
                        if status == 204:
                            print(f"✅ [Account #{account}] Locked multitrade.")
                            await asyncio.sleep(random.uniform(4, 6))  # Wait for Karuta multitrade message to update
                            multitrade_confirm_message = await get_karuta_message(token, account, KARUTA_MULTITRADE_CONFIRM_MESSAGE, RATE_LIMIT)
                            # Find ✅ button
                            check_payload = await find_button(account, '✅', multitrade_confirm_message)
                            if check_payload is not None:
                                async with session.post(INTERACTION_URL, headers = headers, json = check_payload) as check_resp:
                                    status = check_resp.status
                                    if status == 204:
                                        print(f"✅ [Account #{account}] Confirmed multitrade.")
                                    else:
                                        print(f"❌ [Account #{account}] Confirm multitrade failed: Error code {status}.")
                        else:
                            print(f"❌ [Account #{account}] Lock multitrade failed: Error code {status}.")

async def check_multiburn(token: str, account: int, command: str):
    if command.startswith(f"{KARUTA_PREFIX}multiburn") or command.startswith(f"{KARUTA_PREFIX}mb"):
        await asyncio.sleep(random.uniform(4, 6))  # Wait for Karuta multiburn message
        multiburn_initial_message = await get_karuta_message(token, account, KARUTA_MULTIBURN_TITLE, RATE_LIMIT)
        if multiburn_initial_message and multiburn_initial_message not in multiburn_initial_messages:
            await asyncio.sleep(3)  # Longer delay to wait for check button to enable
            multiburn_initial_messages.append(multiburn_initial_message)
            # Find ☑️ button
            payload = await find_button(account, '☑️', multiburn_initial_message)
            if payload is not None:
                async with aiohttp.ClientSession() as session:
                    headers = get_headers(token)
                    async with session.post(INTERACTION_URL, headers = headers, json = payload) as resp:
                        status = resp.status
                        if status == 204:
                            print(f"✅ [Account #{account}] Confirmed initial (0/2) multiburn.")
                        else:
                            print(f"❌ [Account #{account}] Confirm initial (0/2) multiburn failed: Error code {status}.")

async def confirm_multiburn(token: str, account: int, command: str):
    if command == KARUTA_MULTIBURN_COMMAND:
        multiburn_fire_message = await get_karuta_message(token, account, KARUTA_MULTIBURN_TITLE, RATE_LIMIT)
        if multiburn_fire_message and multiburn_fire_message not in multiburn_fire_messages:
            multiburn_fire_messages.append(multiburn_fire_message)
            # Find 🔥 button
            fire_payload = await find_button(account, '🔥', multiburn_fire_message)
            if fire_payload is not None:
                async with aiohttp.ClientSession() as session:
                    headers = get_headers(token)
                    async with session.post(INTERACTION_URL, headers = headers, json = fire_payload) as fire_resp:
                        status = fire_resp.status
                        if status == 204:
                            print(f"✅ [Account #{account}] Confirmed initial (1/2) multiburn.")
                            await asyncio.sleep(random.uniform(4, 6))  # Wait for Karuta multiburn message to update
                            multiburn_confirm_message = await get_karuta_message(token, account, KARUTA_MULTIBURN_TITLE, RATE_LIMIT)
                            # Find ✅ button
                            check_payload = await find_button(account, '✅', multiburn_confirm_message)
                            if check_payload is not None:
                                async with session.post(INTERACTION_URL, headers = headers, json = check_payload) as check_resp:
                                    status = check_resp.status
                                    if status == 204:
                                        print(f"✅ [Account #{account}] Confirmed final (2/2) multiburn.")
                                    else:
                                        print(f"❌ [Account #{account}] Confirm final (2/2) multiburn failed: Error code {status}.")
                        else:
                            print(f"❌ [Account #{account}] Confirm initial (1/2) multiburn failed: Error code {status}.")

async def message_command():
    while True:
        send, account, command = await check_command(random.choice(tokens))  # Use a random account to check for message commands
        if account and command:
            if account == ALL_ACCOUNT_FLAG:
                for index, token in enumerate(tokens):
                    account = index + 1
                    await send_message(token, account, command, RATE_LIMIT)  # Won't retry even if rate-limited (so it doesn't interfere with drops/grabs)
                    await asyncio.sleep(random.uniform(1, 3))
            else:
                token = tokens[account - 1]
                if send:
                    await send_message(token, account, command, RATE_LIMIT)
                await check_card_transfer(token, account, command)
                await check_multitrade(token, account, command)
                await check_multiburn(token, account, command)
                await confirm_multiburn(token, account, command)
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
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=20"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                messages = await resp.json()
                try:
                    for msg in messages:
                        if msg.get('author', {}).get('id') == KARUTA_BOT_ID:
                            if search_content == KARUTA_DROP_MESSAGE in msg.get('content', '') and KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', ''):
                                print(f"✅ [Account #{account}] Retrieved drop message.")
                                return msg
                            elif search_content == KARUTA_CARD_TRANSFER_TITLE == msg['embeds'][0].get('title'):
                                print(f"✅ [Account #{account}] Retrieved card transfer message.")
                                return msg
                            elif search_content == KARUTA_MULTITRADE_LOCK_MESSAGE in msg.get('content', ''):
                                print(f"✅ [Account #{account}] Retrieved multitrade lock message.")
                                return msg
                            elif search_content == KARUTA_MULTITRADE_CONFIRM_MESSAGE in msg.get('content', ''):
                                print(f"✅ [Account #{account}] Retrieved multitrade confirm message.")
                                return msg
                            elif search_content == KARUTA_MULTIBURN_TITLE == msg['embeds'][0].get('title'):
                                print(f"✅ [Account #{account}] Retrieved multiburn message.")
                                return msg
                except Exception as e:
                    # Usually caused by msg['embeds'] not existing (invalid message command)
                    print(f"❌ [Account #{account}] Retrieve message failed: Message '{search_content}' not found in recent messages.")
                    return None
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
        f"{KARUTA_PREFIX}c o:wl",
        f"{KARUTA_PREFIX}c o:p",
        f"{KARUTA_PREFIX}c o:eff",
        f"{KARUTA_PREFIX}cardinfo",
        f"{KARUTA_PREFIX}ci",
        f"{KARUTA_PREFIX}cd",
        f"{KARUTA_PREFIX}daily"
    ]
    emojis = ['1️⃣', '2️⃣', '3️⃣']
    
    while True:
        for index, token in enumerate(tokens):
            print(f"\n{datetime.now().strftime("%I:%M:%S %p").lstrip("0")}")  # Timestamp
            account = index + 1
            drop_message = random.choice(drop_messages) + random.choice(random_addon)  # Randomize message
            sent = await send_message(token, account, drop_message, 0)
            if sent:
                await asyncio.sleep(random.uniform(4, 6))  # Wait for drop message to fully load
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
    card_transfer_messages = []
    multitrade_messages = []
    multiburn_initial_messages = []
    multiburn_fire_messages = []
    asyncio.run(main())