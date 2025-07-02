from token_getter import TokenGetter
from command_checker import CommandChecker
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

class MessageBotter():
    def __init__(self):
        # Customize these settings
        self.TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
        self.SERVER_ID = ""  # Enter your target server
        self.CHANNEL_ID = ""  # Enter your target channel
        self.KARUTA_PREFIX = "k"  # Karuta's bot prefix
        self.MESSAGE_COMMAND_TOGGLE = True  # Enable message commands
        self.RATE_LIMIT = 3  # Maximum number of rate limits before giving up

        # Do not modify these constants
        self.KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID
        self.KARUTA_DROP_MESSAGE = "is dropping 3 cards!"
        self.KARUTA_EXPIRED_DROP_MESSAGE = "This drop has expired and the cards can no longer be grabbed."

        self.KARUTA_CARD_TRANSFER_TITLE = "Card Transfer"

        self.KARUTA_MULTITRADE_LOCK_MESSAGE = "Both sides must lock in before proceeding to the next step."
        self.KARUTA_MULTITRADE_CONFIRM_MESSAGE = "This trade has been locked."

        self.KARUTA_MULTIBURN_TITLE = "Burn Cards"

        self.EMOJI_MAP = {
            '1️⃣': '[1]',
            '2️⃣': '[2]',
            '3️⃣': '[3]'
        }

        # Construct realistic Discord browser headers
        self.token_headers = {}
        self.tokens = []
        self.executed_commands = []
        self.card_transfer_messages = []
        self.multitrade_messages = []
        self.multiburn_initial_messages = []
        self.multiburn_fire_messages = []

    def get_headers(self, token: str):
        if token not in self.token_headers:
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

            self.token_headers[token] = {
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
                    "location_guild_id": self.SERVER_ID,
                    "location_channel_id": self.CHANNEL_ID,
                    "location_channel_type": 1,
                }).encode()).decode()
            }
        return self.token_headers[token]

    async def send_message(self, token: str, account: int, content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{self.CHANNEL_ID}/messages"
        headers = self.get_headers(token)
        payload = {
            "content": content,
            "tts": False,
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                status = resp.status
                if status == 200:
                    print(f"✅ [Account #{account}] Sent message '{content}'.")
                elif status == 401:
                    print(f"❌ [Account #{account}] Message '{content}' failed: Invalid token.")
                elif status == 403:
                    print(f"❌ [Account #{account}] Message '{content}' failed: Token banned or no permission.")
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1  # seconds
                    print(f"⚠️ [Account #{account}] Message '{content}' failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    await self.send_message(token, account, content, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Message '{content}' failed: Error code {status}.")
                return status == 200

    async def get_karuta_message(self, token: str, account: int, search_content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{self.CHANNEL_ID}/messages?limit=20"
        headers = self.get_headers(token)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                status = resp.status
                if status == 200:
                    messages = await resp.json()
                    try:
                        for msg in messages:
                            if msg.get('author', {}).get('id') == self.KARUTA_BOT_ID:
                                if search_content == self.KARUTA_DROP_MESSAGE and self.KARUTA_DROP_MESSAGE in msg.get('content', '') and self.KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', ''):
                                    print(f"✅ [Account #{account}] Retrieved drop message.")
                                    return msg
                                elif search_content == self.KARUTA_CARD_TRANSFER_TITLE and msg.get('embeds') and self.KARUTA_CARD_TRANSFER_TITLE == msg['embeds'][0].get('title'):
                                    print(f"✅ [Account #{account}] Retrieved card transfer message.")
                                    return msg
                                elif search_content == self.KARUTA_MULTITRADE_LOCK_MESSAGE and self.KARUTA_MULTITRADE_LOCK_MESSAGE in msg.get('content', ''):
                                    print(f"✅ [Account #{account}] Retrieved multitrade lock message.")
                                    return msg
                                elif search_content == self.KARUTA_MULTITRADE_CONFIRM_MESSAGE and self.KARUTA_MULTITRADE_CONFIRM_MESSAGE in msg.get('content', ''):
                                    print(f"✅ [Account #{account}] Retrieved multitrade confirm message.")
                                    return msg
                                elif search_content == self.KARUTA_MULTIBURN_TITLE and msg.get('embeds') and self.KARUTA_MULTIBURN_TITLE == msg['embeds'][0].get('title'):
                                    print(f"✅ [Account #{account}] Retrieved multiburn message.")
                                    return msg
                    except (KeyError, IndexError):
                        pass
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1
                    print(f"⚠️ [Account #{account}] Retrieve message failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    return await self.get_karuta_message(token, account, search_content, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Retrieve message failed: Error code {status}.")
                    return None
                print(f"❌ [Account #{account}] Retrieve message failed: Message '{search_content}' not found in recent messages.")
                return None

    async def add_reaction(self, token: str, account: int, message_id: str, emoji: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{self.CHANNEL_ID}/messages/{message_id}/reactions/{emoji}/@me"
        headers = self.get_headers(token)
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=headers) as resp:
                status = resp.status
                card_number = self.EMOJI_MAP.get(emoji)
                if status == 204:
                    print(f"✅ [Account #{account}] Grabbed card {card_number}.")
                elif status == 401:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Invalid token.")
                elif status == 403:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Token banned or no permission.")
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1
                    print(f"⚠️ [Account #{account}] Grab card {card_number} failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    await self.add_reaction(token, account, message_id, emoji, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Error code {status}.")

    async def run(self):
        if self.MESSAGE_COMMAND_TOGGLE:
            command_checker = CommandChecker(
                main = self,
                tokens = self.tokens,
                server_id = self.SERVER_ID,
                channel_id = self.CHANNEL_ID,
                karuta_prefix = self.KARUTA_PREFIX,
                karuta_bot_id = self.KARUTA_BOT_ID,
                karuta_drop_message = self.KARUTA_DROP_MESSAGE,
                karuta_expired_drop_message = self.KARUTA_EXPIRED_DROP_MESSAGE,
                karuta_card_transfer_title = self.KARUTA_CARD_TRANSFER_TITLE,
                karuta_multitrade_lock_message = self.KARUTA_MULTITRADE_LOCK_MESSAGE,
                karuta_multitrade_confirm_message = self.KARUTA_MULTITRADE_CONFIRM_MESSAGE,
                karuta_multiburn_title = self.KARUTA_MULTIBURN_TITLE,
                rate_limit = self.RATE_LIMIT
            )
            asyncio.create_task(command_checker.run())
            print("\n🤖 Message commands enabled.")
        else:
            print("\n🤖 Message commands disabled.")

        num_account = len(self.tokens)
        if num_account == 0:
            input("⛔ Token Error ⛔\nNo tokens found. Please check your account info.")
            sys.exit()
        delay = 30 * 60 / num_account
        grab_pointer = 0 if num_account < 3 else num_account - 3
        random_addon = ['', ' ', ' !', ' :D', ' w']
        drop_messages = [f"{self.KARUTA_PREFIX}drop", f"{self.KARUTA_PREFIX}d"]
        random_messages = [
            f"{self.KARUTA_PREFIX}reminders", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}lookup",
            f"{self.KARUTA_PREFIX}lu", f"{self.KARUTA_PREFIX}vote", f"{self.KARUTA_PREFIX}view",
            f"{self.KARUTA_PREFIX}v", f"{self.KARUTA_PREFIX}collection", f"{self.KARUTA_PREFIX}c",
            f"{self.KARUTA_PREFIX}c o:wl", f"{self.KARUTA_PREFIX}c o:p", f"{self.KARUTA_PREFIX}c o:eff",
            f"{self.KARUTA_PREFIX}cardinfo", f"{self.KARUTA_PREFIX}ci", f"{self.KARUTA_PREFIX}cd",
            f"{self.KARUTA_PREFIX}daily"
        ]
        emojis = ['1️⃣', '2️⃣', '3️⃣']

        while True:
            for index, token in enumerate(self.tokens):
                print(f"\n{datetime.now().strftime('%I:%M:%S %p').lstrip('0')}")
                account = index + 1
                drop_message = random.choice(drop_messages) + random.choice(random_addon)
                sent = await self.send_message(token, account, drop_message, 0)
                if sent:
                    await asyncio.sleep(random.uniform(3, 6))
                    karuta_message = await self.get_karuta_message(token, account, self.KARUTA_DROP_MESSAGE, 0)
                    if karuta_message:
                        karuta_message_id = karuta_message.get('id')
                        random.shuffle(emojis)
                        for i in range(3):
                            emoji = emojis[i]
                            grab_index = (grab_pointer + i) % num_account
                            grab_token = self.tokens[grab_index]
                            grab_account = grab_index + 1
                            await self.add_reaction(grab_token, grab_account, karuta_message_id, emoji, 0)
                            await asyncio.sleep(random.uniform(0, 1))
                            random_message = random.choice(random_messages)
                            await self.send_message(grab_token, grab_account, random_message, self.RATE_LIMIT)
                else:
                    if self.TERMINAL_VISIBILITY:
                        hwnd = win32console.GetConsoleWindow()
                        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                        win32gui.SetForegroundWindow(hwnd)
                        input("⛔ Request Error ⛔\nMalformed request. Possible causes include:\n 1. Invalid/expired token\n 2. Incorrectly inputted server/channel/bot ID\nPress `Enter` to restart the script.")
                        ctypes.windll.shell32.ShellExecuteW(
                            None, None, sys.executable, " ".join(sys.argv), None, self.TERMINAL_VISIBILITY
                        )
                    sys.exit()
                grab_pointer = (grab_pointer + 3) % num_account
                await asyncio.sleep(delay + random.uniform(0, max(20, 120 / num_account)))

if __name__ == "__main__":
    bot = MessageBotter()
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, bot.TERMINAL_VISIBILITY
        )
        sys.exit()
    if not all([bot.SERVER_ID, bot.CHANNEL_ID, bot.KARUTA_BOT_ID]):
        input("⛔ Configuration Error ⛔\nPlease use a valid server ID, channel ID, and Karuta bot ID in [main.py](cci:7://file:///c:/Users/andyw/Documents/Projects/Discord-Message-Botter/message_botter/main.py:0:0-0:0).")
        sys.exit()
    bot.tokens = TokenGetter().main()
    asyncio.run(bot.run())