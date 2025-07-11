from token_extractor import TokenExtractor
from command_checker import CommandChecker
from datetime import datetime
from collections import defaultdict
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
import math
import time

class MessageBotter():
    def __init__(self):
        ### CUSTOMIZE THESE SETTINGS ###
        self.COMMAND_USER_ID = ""  # Enter the user ID of the account that can use message commands
        self.COMMAND_CHANNEL_ID = ""  # Enter your command channel to send message commands
        # Enter your drop channels as strings separated by commas
        self.DROP_CHANNEL_IDS = [
            "",
        ]
        self.TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
        self.KARUTA_PREFIX = "k"  # Karuta's bot prefix
        self.SHUFFLE_DROP_CHANNELS = True  # Improve randomness by changing where accounts drop every time the script runs
        self.MESSAGE_COMMAND_TOGGLE = True  # Enable message commands
        self.RATE_LIMIT = 3  # Maximum number of rate limits before giving up

        ### DO NOT MODIFY THESE CONSTANTS ###
        self.KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID
        self.KARUTA_DROP_MESSAGE = "is dropping 3 cards!"
        self.KARUTA_EXPIRED_DROP_MESSAGE = "This drop has expired and the cards can no longer be grabbed."

        self.KARUTA_CARD_TRANSFER_TITLE = "Card Transfer"

        self.KARUTA_MULTITRADE_LOCK_MESSAGE = "Both sides must lock in before proceeding to the next step."
        self.KARUTA_MULTITRADE_CONFIRM_MESSAGE = "This trade has been locked."

        self.KARUTA_MULTIBURN_TITLE = "Burn Cards"

        self.RANDOM_ADDON = ['', ' ', ' !', ' :D', ' w']
        self.DROP_MESSAGES = [f"{self.KARUTA_PREFIX}drop", f"{self.KARUTA_PREFIX}d"]
        self.RANDOM_MESSAGES = [
            f"{self.KARUTA_PREFIX}reminders", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}lookup",
            f"{self.KARUTA_PREFIX}lu", f"{self.KARUTA_PREFIX}vote", f"{self.KARUTA_PREFIX}view",
            f"{self.KARUTA_PREFIX}v", f"{self.KARUTA_PREFIX}collection", f"{self.KARUTA_PREFIX}c",
            f"{self.KARUTA_PREFIX}c o:wl", f"{self.KARUTA_PREFIX}c o:p", f"{self.KARUTA_PREFIX}c o:eff",
            f"{self.KARUTA_PREFIX}cardinfo", f"{self.KARUTA_PREFIX}ci", f"{self.KARUTA_PREFIX}cd",
            f"{self.KARUTA_PREFIX}daily", f"{self.KARUTA_PREFIX}monthly", "bruh", "gg", "lmao", "wtf", "omg"
        ]
        self.EMOJIS = ['1️⃣', '2️⃣', '3️⃣']
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
            chrome_version = random.choice(["138.0.7204.119", "138.0.7204.46", "138.0.7204.100"])  # Recent Chrome versions (iOS, Android, and Desktop Chrome respectively) (July 2025)
            build_number = random.choice([301456, 305789, 378984])  # Random Discord build version numbers
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
                json.dumps(super_properties, separators = (',', ':')).encode()
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
                    "location_channel_id": self.token_channel_dict[token],
                    "location_channel_type": 1,
                }).encode()).decode()
            }
        return self.token_headers[token]

    async def send_message(self, token: str, account: int, content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{self.token_channel_dict[token]}/messages"
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
        url = f"https://discord.com/api/v10/channels/{self.token_channel_dict[token]}/messages?limit=20"
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
        url = f"https://discord.com/api/v10/channels/{self.token_channel_dict[token]}/messages/{message_id}/reactions/{emoji}/@me"
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

    async def run_command_checker(self):
        if self.MESSAGE_COMMAND_TOGGLE:
            command_checker = CommandChecker(
                main = self,
                tokens = self.tokens,
                command_user_id = self.COMMAND_USER_ID,
                command_channel_id = self.COMMAND_CHANNEL_ID,
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

    async def set_token_dictionaries(self):
        self.token_channel_dict = {}
        for index, token in enumerate(self.tokens):
            self.token_channel_dict[token] = self.DROP_CHANNEL_IDS[math.floor(index / 3)]  # Max 3 accounts per channel
        self.channel_token_dict = defaultdict(list)
        for k, v in self.token_channel_dict.items():
            self.channel_token_dict[v].append(k)

    async def drop_and_grab(self, token: str, account: int, channel_tokens: list[str]):
        print(f"\n{datetime.now().strftime('%I:%M:%S %p').lstrip('0')}")
        num_channel_tokens = len(channel_tokens)
        drop_message = random.choice(self.DROP_MESSAGES) + random.choice(self.RANDOM_ADDON)
        sent = await self.send_message(token, account, drop_message, 0)
        if sent:
            await asyncio.sleep(random.uniform(3, 6))
            karuta_message = await self.get_karuta_message(token, account, self.KARUTA_DROP_MESSAGE, 0)
            if karuta_message:
                karuta_message_id = karuta_message.get('id')
                random.shuffle(self.EMOJIS)
                for i in range(num_channel_tokens):
                    emoji = self.EMOJIS[i]
                    grab_token = channel_tokens[i]
                    grab_account = self.tokens.index(grab_token) + 1
                    await self.add_reaction(grab_token, grab_account, karuta_message_id, emoji, 0)
                    await asyncio.sleep(random.uniform(0.5, 2))
                scrambled_channel_tokens = random.sample(channel_tokens, len(channel_tokens))
                for i in range(num_channel_tokens):
                    if random.choice([True, False]):
                        grab_token = scrambled_channel_tokens[i]
                        grab_account = self.tokens.index(grab_token) + 1
                        for _ in range(random.randint(1, 3)):
                            random_message = random.choice(self.RANDOM_MESSAGES)
                            await self.send_message(grab_token, grab_account, random_message, self.RATE_LIMIT)
                            await asyncio.sleep(random.uniform(1, 3))
        else:
            if self.TERMINAL_VISIBILITY:
                hwnd = win32console.GetConsoleWindow()
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                input(f"⛔ Request Error ⛔\nMalformed request on Account #{account}. Possible reasons include:\n 1. Invalid/expired token\n 2. Incorrectly inputted server/channel/bot ID\nPress `Enter` to restart the script.")
                ctypes.windll.shell32.ShellExecuteW(
                    None, None, sys.executable, " ".join(sys.argv), None, self.TERMINAL_VISIBILITY
                )
            else:
                sys.exit()

    async def run_bot(self):
        await self.run_command_checker()
        await self.set_token_dictionaries()
        self.min_num_account_per_channel = len(self.channel_token_dict[self.DROP_CHANNEL_IDS[-1]])  # Get the minimum number of accounts in channels (ideally 3 (if number of accounts is a multiple of 3))
        self.DELAY = 30 * 60 / self.min_num_account_per_channel  # Ideally 10 min delay per account (3 accounts)
        if self.SHUFFLE_DROP_CHANNELS:
            random.shuffle(self.DROP_CHANNEL_IDS)
        self.start_time = time.time()
        while True:
            for index in range(self.min_num_account_per_channel):
                if time.time() - self.start_time >= 12 * 60 * 60:  # 12 hours
                    input("⚠️ Script Runtime Warning ⚠️\nThe script has been running for 12 hours. Automatically pausing to avoid ban risk...\nPress `Enter` if you wish to continue running the script.")
                scrambled_drop_channel_ids = random.sample(self.DROP_CHANNEL_IDS, len(self.DROP_CHANNEL_IDS))
                for channel_id in scrambled_drop_channel_ids:
                    channel_tokens = self.channel_token_dict[channel_id]
                    token = channel_tokens[index]
                    await self.drop_and_grab(token, self.tokens.index(token) + 1, channel_tokens)
                    await asyncio.sleep(random.uniform(1, 50))
                await asyncio.sleep(self.DELAY + random.uniform(0, 40))

if __name__ == "__main__":
    bot = MessageBotter()
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, bot.TERMINAL_VISIBILITY
        )
        sys.exit()
    try:
        if (
            (bot.COMMAND_USER_ID != "" and not bot.COMMAND_USER_ID.isdigit())
            or not bot.COMMAND_CHANNEL_ID.isdigit()
            or not all(id.isdigit() for id in bot.DROP_CHANNEL_IDS)
            or not bot.KARUTA_BOT_ID.isdigit()
        ):
            input("⛔ Configuration Error ⛔\nPlease enter non-empty, numeric strings for the command user ID, command channel ID, drop channel ID(s), and Karuta bot ID in main.py.")
            sys.exit()
    except AttributeError:
        input("⛔ Configuration Error ⛔\nPlease enter strings (not integers) for the command user ID, command channel ID, drop channel ID(s), and Karuta bot ID in main.py.")
        sys.exit()
    bot.tokens = TokenExtractor().main(len(bot.DROP_CHANNEL_IDS))
    asyncio.run(bot.run_bot())