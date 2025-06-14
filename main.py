import aiohttp
import asyncio
import base64
import json
import random
import sys
import ctypes

# Flag to check if script relaunched
RELAUNCH_FLAG = "--no-relaunch"

# Replace with your real user tokens
tokens = [
    "",
]

channel_id = ""  # Replace with your actual target channel

# Construct realistic Discord browser headers
def get_headers(token: str):
    super_properties = {
        "os": "Windows",
        "browser": "Chrome",
        "device": "",
        "system_locale": "en-US",
        "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/114.0.0.0 Safari/537.36",
        "browser_version": "114.0.0.0",
        "os_version": "10",
        "referrer": "",
        "referring_domain": "",
        "referrer_current": "",
        "referring_domain_current": "",
        "release_channel": "stable",
        "client_build_number": 272593,
        "client_event_source": None,
    }

    super_properties_b64 = base64.b64encode(
        json.dumps(super_properties, separators=(',', ':')).encode()
    ).decode()

    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": super_properties["browser_user_agent"],
        "X-Super-Properties": super_properties_b64,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://discord.com",
        "Referer": f"https://discord.com/channels/@me",
    }

    return headers

async def send_message(token: str, content: str):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = get_headers(token)
    payload = {
        "content": content,
        "tts": False,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            status = resp.status
            body = await resp.text()
            print(f"[{token[:5]}...] Status: {status} | Response: {body[:100]}")

async def main():
    delay = 30 / len(tokens)
    for i, token in enumerate(tokens):
        message = f"Automated message from account #{i+1}"
        await send_message(token, message)
        rand_delay = random.randint(3, 45)
        await asyncio.sleep(delay + rand_delay)

if __name__ == "__main__":
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + ["--no-relaunch"]), None, 1
        )
        sys.exit()
    asyncio.run(main())