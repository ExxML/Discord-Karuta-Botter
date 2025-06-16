from token_getter import TokenGetter
import aiohttp
import asyncio
import base64
import json
import random
import sys
import ctypes

SERVER_ID = ""  # Enter your target server
CHANNEL_ID = ""  # Enter your target channel

# Construct realistic Discord browser headers
def get_headers(token: str):
    # Base super properties copied from real Discord browser traffic
    super_properties = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.5735.134 Safari/537.36"
        ),
        "browser_version": "114.0.5735.134",
        "os_version": "10",
        "referrer": "https://discord.com/channels/@me",
        "referring_domain": "discord.com",
        "referrer_current": "https://discord.com/channels/@me",
        "referring_domain_current": "discord.com",
        "release_channel": "stable",
        "client_build_number": 272593,
        "client_event_source": None
    }

    x_super_props = base64.b64encode(
        json.dumps(super_properties, separators=(',', ':')).encode()
    ).decode()

    headers = {
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

    return headers

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
            body = await resp.text()
            print(f"[Account #{tokens.index(token) + 1}] Status: {status} | Response: {body}")

async def main():
    if len(tokens) == 0:
        print("No tokens found. Please check your accounts.")
        return
    delay = 30*60 / len(tokens)  # Karuta drop cooldown is 30 mins- set delay to spread out drops
    while True:
        for i, token in enumerate(tokens):
            message = f"Automated message from account #{i+1}"
            await send_message(token, message)
            rand_delay = random.randint(0, 90)  # Random additional delay to avoid detection
            await asyncio.sleep(delay + rand_delay)

if __name__ == "__main__":
    # Flag to check if script relaunched
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, 1  # Set to 0 to hide terminal
        )
        sys.exit()
    tokens = TokenGetter().main()
    asyncio.run(main())