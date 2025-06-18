from token_getter import TokenGetter
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

TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible
SERVER_ID = ""  # Enter your target server
CHANNEL_ID = ""  # Enter your target channel
KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID

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

async def send_message(token: str, content: str):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = get_headers(token)
    payload = {
        "content": content,
        "tts": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers = headers, json = payload) as resp:
            status = resp.status
            account = tokens.index(token) + 1
            if status == 200:
                print(f"[Account #{account}] Dropped cards successfully.")
            elif status == 401:
                print(f"[Account #{account}] Drop failed: Invalid token.")
            elif status == 403:
                print(f"[Account #{account}] Drop failed: Token banned or no permission.")
            elif status == 429:
                print(f"[Account #{account}] Drop failed: Rate limited.")
            else:
                print(f"[Account #{account}] Drop failed: Error code {status}.")
            return (await resp.json()).get('id') if status == 200 else None

async def add_reaction(token: str, message_id: str, emoji: str):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{message_id}/reactions/{emoji}/@me"
    headers = get_headers(token)
    
    async with aiohttp.ClientSession() as session:
        async with session.put(url, headers = headers) as resp:
            status = resp.status
            account = tokens.index(token) + 1
            if status == 204:
                print(f"[Account #{account}] Grabbed card {emoji} successfully.")
            elif status == 401:
                print(f"[Account #{account}] Grab card {emoji} failed: Invalid token.")
            elif status == 403:
                print(f"[Account #{account}] Grab card {emoji} failed: Token banned or no permission.")
            elif status == 429:
                retry_after = (await resp.json()).get('retry_after', 1)
                print(f"[Account #{account}] Grab card {emoji} failed: Rate limited, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                await add_reaction(token, message_id, emoji)  # Retry reaction
            else:
                print(f"[Account #{account}] Grab card {emoji} failed: Error code {status}.")

async def get_user_id(token: str):
    url = "https://discord.com/api/v10/users/@me"
    headers = get_headers(token)
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            if resp.status == 200:
                return (await resp.json()).get('id')
            return None

async def get_karuta_drop_message(token: str):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=2"
    headers = get_headers(token)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers = headers) as resp:
            if resp.status == 200:
                user_id = await get_user_id(token)
                messages = await resp.json()
                for msg in messages:
                    if msg.get('author', {}).get('id') == KARUTA_BOT_ID and f"<@{user_id}> is dropping 3 cards!" == msg.get('content', ''): # Return ID only if Karuta mentions user
                        return msg.get('id')
            elif resp.status == 429:
                retry_after = (await resp.json()).get('retry_after', 5)
                print(f"[Account #{tokens.index(token) + 1}] Retrieve drop ID failed: Rate limited on message fetch, retrying after {retry_after}s.")
                await asyncio.sleep(retry_after)
                return await get_karuta_drop_message(token)  # Retry
            else:
                print(f"[Account #{tokens.index(token) + 1}] Retrieve drop ID failed: Error code {resp.status} on message fetch.")
                return None
            print(f"[Account #{tokens.index(token) + 1}] Retrieve drop ID failed: No drop found in the last 5 messages.")
            return None

async def main():
    if len(tokens) == 0:
        print("No tokens found. Please check your accounts.")
        return
    delay = 30 * 60 / len(tokens)  # Karuta drop cooldown is 30 mins- set delay to spread out drops
    random_addon = random.choice(['', ' ', ' !', ' :D', ' drop'])
    drop_messages = [f"kdrop{random_addon}", f"kd{random_addon}"]  # Vary to avoid detection
    emojis = ['1️⃣', '2️⃣', '3️⃣']
    
    while True:
        for i, token in enumerate(tokens):
            message = random.choice(drop_messages)  # Randomize message
            message_id = await send_message(token, message)
            if message_id:
                # Wait for Karuta's response
                await asyncio.sleep(random.uniform(5, 7))
                karuta_message_id = await get_karuta_drop_message(token)
                if karuta_message_id:
                    random.shuffle(emojis)
                    for emoji in emojis:
                        await asyncio.sleep(random.uniform(0.5, 3))  # Random delay between reactions
                        await add_reaction(token, karuta_message_id, emoji)
                else:
                    print(f"[Account #{i + 1}] Grab failed: No drop message found.")
            else:
                # Set terminal window on top to notify user of invalid token
                if TERMINAL_VISIBILITY:
                    hwnd = win32console.GetConsoleWindow()
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                    win32gui.SetForegroundWindow(hwnd)
                    input("At least one token is invalid. Press `Enter` to restart the script.")
                    ctypes.windll.shell32.ShellExecuteW(
                        None, None, sys.executable, " ".join(sys.argv), None, TERMINAL_VISIBILITY
                    )
                sys.exit()
            await asyncio.sleep(delay + random.uniform(0, 60))  # Random delay between accounts

if __name__ == "__main__":
    # Flag to check if script relaunched
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, TERMINAL_VISIBILITY
        )
        sys.exit()
    tokens = TokenGetter().main()
    asyncio.run(main())