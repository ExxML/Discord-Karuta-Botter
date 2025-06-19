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

TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
SERVER_ID = ""  # Enter your target server
CHANNEL_ID = ""  # Enter your target channel

KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID
KARUTA_PREFIX = "k"  # Karuta's bot prefix
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
                retry_after = (await resp.json()).get('retry_after', 5)
                print(f"⚠️ [Account #{account}] Message '{content}' failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await send_message(token, account, content, rate_limited)  # Retry drop
            else:
                print(f"❌ [Account #{account}] Message '{content}' failed: Error code {status}.")
            return status == 200

async def get_user_id(token: str, account: int, rate_limited: int):
    url = "https://discord.com/api/v10/users/@me"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                print(f"✅ [Account #{account}] Retrieved user ID.")
            elif status == 429 and rate_limited < RATE_LIMIT:
                rate_limited += 1
                retry_after = (await resp.json()).get('retry_after', 3)
                print(f"⚠️ [Account #{account}] Retrieve user ID failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await get_user_id(token, account, rate_limited)  # Retry getting user ID
            else:
                print(f"❌ [Account #{account}] Retrieve user ID failed: Error code {status}.")
            return (await resp.json()).get('id') if status == 200 else None

async def get_karuta_drop_message(token: str, account: int, rate_limited: int):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=5"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            status = resp.status
            if status == 200:
                user_id = await get_user_id(token, account, 0)
                if user_id is None:
                    print(f"❌ [Account #{account}] Retrieve drop ID failed: Failed to retrieve user ID.")
                    return None
                messages = await resp.json()
                for msg in messages:
                    if msg.get('author', {}).get('id') == KARUTA_BOT_ID and f"<@{user_id}> is dropping 3 cards!" == msg.get('content', ''): # Return ID only if Karuta mentions user
                        print(f"✅ [Account #{account}] Retrieved drop ID.")
                        return msg.get('id') 
            elif status == 429 and rate_limited < RATE_LIMIT:
                rate_limited += 1
                retry_after = (await resp.json()).get('retry_after', 3)
                print(f"⚠️ [Account #{account}] Retrieve drop ID failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                return await get_karuta_drop_message(token, account, rate_limited)  # Retry getting message ID
            else:
                print(f"❌ [Account #{account}] Retrieve drop ID failed: Error code {status}.")
                return None
            # If status = 200 but no drop found
            print(f"❌ [Account #{account}] Retrieve drop ID failed: No drop found in recent messages.")
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
                retry_after = (await resp.json()).get('retry_after', 3)
                print(f"⚠️ [Account #{account}] Grab card {card_number} failed ({rate_limited}/{RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await add_reaction(token, account, message_id, emoji, rate_limited)  # Retry reaction
            else:
                print(f"❌ [Account #{account}] Grab card {card_number} failed: Error code {status}.")

async def main():
    account_num = len(tokens)
    if account_num == 0:
        input("⛔ Token Error ⛔\nNo tokens found. Please check your account info.")
        sys.exit()
    delay = 30 * 60 / account_num  # Karuta drop cooldown is 30 mins- set delay to spread out drops
    if account_num < 3:
        grab_pointer = 0  # Token pointer for auto-grab
    else:
        grab_pointer = account_num - 3
    random_addon = random.choice(['', ' ', ' !', ' :D', ' w'])  # Variance to avoid detection
    drop_messages = [f"{KARUTA_PREFIX}drop{random_addon}", f"{KARUTA_PREFIX}d{random_addon}"]
    random_messages = [
        f"{KARUTA_PREFIX}reminders", 
        f"{KARUTA_PREFIX}rm",
        f"{KARUTA_PREFIX}lookup",
        f"{KARUTA_PREFIX}lu",
        f"{KARUTA_PREFIX}vote",
        f"{KARUTA_PREFIX}view",
        f"{KARUTA_PREFIX}v",
        f"{KARUTA_PREFIX}collection",
        f"{KARUTA_PREFIX}c"
    ]
    emojis = ['1️⃣', '2️⃣', '3️⃣']
    
    while True:
        for index, token in enumerate(tokens):
            print(f"\n{datetime.now().strftime("%I:%M:%S %p").lstrip("0")}")  # Timestamp
            account = index + 1
            drop_message = random.choice(drop_messages)  # Randomize message
            sent = await send_message(token, account, drop_message, 0)
            if sent:
                await asyncio.sleep(random.uniform(5, 8))  # Wait for drop message to fully load
                karuta_message_id = await get_karuta_drop_message(token, account, 0)
                if karuta_message_id:
                    random.shuffle(emojis)
                    for i in range(0, 3):
                        emoji = emojis[i]
                        grab_index = (grab_pointer + i) % account_num
                        grab_token = tokens[grab_index]
                        grab_account = grab_index + 1
                        await add_reaction(grab_token, grab_account, karuta_message_id, emoji, 0)
                        await asyncio.sleep(random.uniform(0.5, 5))
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
    asyncio.run(main())