from token_extractor import TokenExtractor
from command_checker import CommandChecker
from datetime import datetime, timedelta
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

class DropFailCount:
    def __init__(self, value):
        self.value = value

class MessageBotter():
    def __init__(self):
        ### CUSTOMIZE THESE SETTINGS ###
        # Enter a list of strings containing the user IDs that can use message commands. Leave the list empty to allow any account to use commands.
        self.COMMAND_USER_IDS = [
            "",
        ]
        # Enter your command server and channel (where commands can be sent) as a string. Leave the strings empty to disable message commands.
        self.COMMAND_SERVER_ID = ""
        self.COMMAND_CHANNEL_ID = ""
        # Enter your drop channels as list of strings
        self.DROP_CHANNEL_IDS = [
            "",
        ]
        self.TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
        self.KARUTA_PREFIX = "k"  # (str) Karuta's bot prefix
        self.SHUFFLE_ACCOUNTS = True  # (bool) Improve randomness by shuffling accounts across channels every time the script runs
        self.RATE_LIMIT = 3  # (int) Maximum number of rate limits before giving up
        self.DROP_FAIL_LIMIT = 3  # (int) Maximum number of failed drops across all channels before pausing script. Set to -1 if you wish to disable this limit.
        self.TIME_LIMIT_HOURS_MIN = 5  # (int) MINIMUM time limit in hours before script automatically pauses (to avoid ban risk)
        self.TIME_LIMIT_HOURS_MAX = 10  # (int) MAXIMUM time limit in hours before script automatically pauses (to avoid ban risk)
        self.CHANNEL_SKIP_RATE = 8  # (int) Every time the script runs, there is a 1/self.CHANNEL_SKIP_RATE chance of skipping a channel. Set to -1 if you wish to disable skipping.
        self.DROP_SKIP_RATE = 12  # (int) Every drop, there is a 1/self.DROP_SKIP_RATE chance of skipping the drop. Set to -1 if you wish to disable it skipping.

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
            f"{self.KARUTA_PREFIX}daily", f"{self.KARUTA_PREFIX}monthly", "bruh", "gg", "lmao", "wtf", "omg",
            "dam", "crazy", "look", "wow", "huh", "umm", "hey", "hellooo", "yo"
        ]
        self.EMOJIS = ['1️⃣', '2️⃣', '3️⃣']
        self.EMOJI_MAP = {
            '1️⃣': '[1]',
            '2️⃣': '[2]',
            '3️⃣': '[3]'
        }

        self.TIME_LIMIT_EXCEEDED_MESSAGES = ["stawp", "stoop", "quittin", "q", "exeeting", "exité", "ceeze", "cloze", '🛑', '🚫', '❌', '⛔']

        # Set up variables
        self.token_headers = {}
        self.tokens = []
        self.executed_commands = []
        self.card_transfer_messages = []
        self.multitrade_messages = []
        self.multiburn_initial_messages = []
        self.multiburn_fire_messages = []

    def check_config(self):
        try:
            if not all([
                all(id.isdigit() for id in self.COMMAND_USER_IDS),
                (self.COMMAND_SERVER_ID == "" or self.COMMAND_SERVER_ID.isdigit()),
                (self.COMMAND_CHANNEL_ID == "" or self.COMMAND_CHANNEL_ID.isdigit()),
                all(id.isdigit() for id in self.DROP_CHANNEL_IDS),
                self.KARUTA_BOT_ID.isdigit()
            ]):
                input("⛔ Configuration Error ⛔\nPlease enter non-empty, numeric strings for the command user ID(s), command server/channel ID, drop channel ID(s), and Karuta bot ID in main.py.")
                sys.exit()
        except AttributeError:
            input("⛔ Configuration Error ⛔\nPlease enter strings (not integers) for the command user ID(s), command server/channel ID, drop channel ID(s), and Karuta bot ID in main.py.")
            sys.exit()
        if not all([
            isinstance(self.TERMINAL_VISIBILITY, int),
            isinstance(self.KARUTA_PREFIX, str),
            isinstance(self.SHUFFLE_ACCOUNTS, bool),
            isinstance(self.RATE_LIMIT, int),
            isinstance(self.DROP_FAIL_LIMIT, int),
            isinstance(self.TIME_LIMIT_HOURS_MIN, int),
            isinstance(self.TIME_LIMIT_HOURS_MAX, int),
            isinstance(self.CHANNEL_SKIP_RATE, int),
            isinstance(self.DROP_SKIP_RATE, int),
            self.TERMINAL_VISIBILITY in (0, 1),
            self.RATE_LIMIT >= 0,
            self.TIME_LIMIT_HOURS_MIN >= 0,
            self.TIME_LIMIT_HOURS_MAX >= 0,
            self.CHANNEL_SKIP_RATE != 0,
            self.DROP_SKIP_RATE != 0
        ]):
            input("⛔ Configuration Error ⛔\nPlease enter valid constant values in main.py.")
            sys.exit()
        if self.TIME_LIMIT_HOURS_MIN > self.TIME_LIMIT_HOURS_MAX:
            input("⛔ Configuration Error ⛔\nPlease enter a maximum time limit greater than the minimum time limit in main.py.")
            sys.exit()

    def get_headers(self, token: str, is_command: bool):
        if token not in self.token_headers:
            chrome_version = random.choice(["138.0.7204.119", "138.0.7204.46", "138.0.7204.100"])  # Recent Chrome versions (iOS, Android, and Desktop Chrome respectively) (July 2025)
            build_number = random.choice([381653, 382032, 382201, 382355, 417521])  # Random Discord build version numbers
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
                    "location_channel_id": self.COMMAND_CHANNEL_ID if is_command else self.token_channel_dict[token],
                    "location_channel_type": 1,
                }).encode()).decode()
            }
        return self.token_headers[token]

    async def get_drop_message(self, token: str, account: int, channel_id: str):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=10"
        headers = self.get_headers(token, is_command = False)
        emoji = '3️⃣'  # Wait until the final reaction (3) is added to the drop message
        timeout = 10  # seconds
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            while (time.monotonic() - start_time) < timeout:
                async with session.get(url, headers = headers) as resp:
                    status = resp.status
                    if status == 200:
                        messages = await resp.json()
                        try:
                            for msg in messages:
                                reactions = msg.get('reactions', [])
                                if all([
                                    msg.get('author', {}).get('id') == self.KARUTA_BOT_ID,
                                    any(reaction.get('emoji', {}).get('name') == emoji for reaction in reactions),
                                    self.KARUTA_DROP_MESSAGE in msg.get('content', ''),
                                    self.KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', '')
                                ]):
                                    print(f"✅ [Account #{account}] Retrieved drop message.")
                                    return msg
                        except (KeyError, IndexError):
                            pass
                    elif status == 401:
                        print(f"❌ [Account #{account}] Retrieve drop message failed ({drop_fail_count.value + 1}/{self.DROP_FAIL_LIMIT}): Invalid token.")
                        async with drop_fail_count_lock:
                            drop_fail_count.value += 1
                        return None
                    elif status == 403:
                        print(f"❌ [Account #{account}] Retrieve drop message failed ({drop_fail_count.value + 1}/{self.DROP_FAIL_LIMIT}): Token banned or insufficient permissions.")
                        async with drop_fail_count_lock:
                            drop_fail_count.value += 1
                        return None
                await asyncio.sleep(random.uniform(1, 2))
            print(f"❌ [Account #{account}] Retrieve drop message failed ({drop_fail_count.value + 1}/{self.DROP_FAIL_LIMIT}): Timed out ({timeout}s).")
            async with drop_fail_count_lock:
                drop_fail_count.value += 1
            return None

    async def send_message(self, token: str, account: int, channel_id: str, content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = self.get_headers(token, is_command = False)
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
                    print(f"❌ [Account #{account}] Send message '{content}' failed: Invalid token.")
                elif status == 403:
                    print(f"❌ [Account #{account}] Send message '{content}' failed: Token banned or insufficient permissions.")
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1  # seconds
                    print(f"⚠️ [Account #{account}] Send message '{content}' failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    await self.send_message(token, account, channel_id, content, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Send message '{content}' failed: Error code {status}.")
                return status == 200

    async def get_karuta_message(self, token: str, account: int, channel_id: str, search_content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=20"
        headers = self.get_headers(token, is_command = False)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers = headers) as resp:
                status = resp.status
                if status == 200:
                    messages = await resp.json()
                    try:
                        for msg in messages:
                            if msg.get('author', {}).get('id') == self.KARUTA_BOT_ID:
                                if search_content == self.KARUTA_CARD_TRANSFER_TITLE and msg.get('embeds') and self.KARUTA_CARD_TRANSFER_TITLE == msg['embeds'][0].get('title'):
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
                    return await self.get_karuta_message(token, account, channel_id, search_content, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Retrieve message failed: Error code {status}.")
                    return None
                print(f"❌ [Account #{account}] Retrieve message failed: Message '{search_content}' not found in recent messages.")
                return None

    async def add_reaction(self, token: str, account: int, channel_id: str, message_id: str, emoji: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        headers = self.get_headers(token, is_command = False)
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers = headers) as resp:
                status = resp.status
                card_number = self.EMOJI_MAP.get(emoji)
                if status == 204:
                    print(f"✅ [Account #{account}] Grabbed card {card_number}.")
                elif status == 401:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Invalid token.")
                elif status == 403:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Token banned or insufficient permissions.")
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1
                    print(f"⚠️ [Account #{account}] Grab card {card_number} failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    await self.add_reaction(token, account, channel_id, message_id, emoji, rate_limited)
                else:
                    print(f"❌ [Account #{account}] Grab card {card_number} failed: Error code {status}.")

    async def run_command_checker(self):
        if all([self.COMMAND_SERVER_ID, self.COMMAND_CHANNEL_ID]):  # If command server id AND channel id field is not empty
            command_checker = CommandChecker(
                main = self,
                tokens = self.tokens,
                command_user_ids = self.COMMAND_USER_IDS,
                command_server_id = self.COMMAND_SERVER_ID,
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
        tokens = self.shuffled_tokens if self.shuffled_tokens else self.tokens
        for index, token in enumerate(tokens):
            self.token_channel_dict[token] = self.DROP_CHANNEL_IDS[math.floor(index / 3)]  # Max 3 accounts per channel
        self.channel_token_dict = defaultdict(list)
        for k, v in self.token_channel_dict.items():
            self.channel_token_dict[v].append(k)

    async def drop_and_grab(self, token: str, account: int, channel_id: str, channel_tokens: list[str]):
        num_channel_tokens = len(channel_tokens)
        drop_message = random.choice(self.DROP_MESSAGES) + random.choice(self.RANDOM_ADDON)
        sent = await self.send_message(token, account, channel_id, drop_message, 0)
        if sent:
            drop_message = await self.get_drop_message(token, account, channel_id)
            if drop_message:
                drop_message_id = drop_message.get('id')
                random.shuffle(self.EMOJIS)  # Shuffle emojis for random emoji order
                random.shuffle(channel_tokens)  # Shuffle tokens for random emoji assignment
                for i in range(num_channel_tokens):
                    emoji = self.EMOJIS[i]
                    grab_token = channel_tokens[i]
                    grab_account = self.tokens.index(grab_token) + 1
                    await self.add_reaction(grab_token, grab_account, channel_id, drop_message_id, emoji, 0)
                    await asyncio.sleep(random.uniform(0.5, 5))
                random.shuffle(channel_tokens)  # Shuffle tokens again for random order messages
                for i in range(num_channel_tokens):
                    if random.choice([True, False]):  # 50% chance of sending messages
                        grab_token = channel_tokens[i]
                        grab_account = self.tokens.index(grab_token) + 1
                        for _ in range(random.randint(1, 3)):
                            random_message = random.choice(self.RANDOM_MESSAGES)
                            await self.send_message(grab_token, grab_account, channel_id, random_message, self.RATE_LIMIT)
                            await asyncio.sleep(random.uniform(1, 4))
        else:
            if self.TERMINAL_VISIBILITY:
                hwnd = win32console.GetConsoleWindow()
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                input(f"⛔ Request Error ⛔\nMalformed request on Account #{account}. Possible reasons include:" +
                        f"\n 1. Invalid/expired token\n 2. Incorrectly inputted server/channel/bot ID\nPress `Enter` to restart the script.")
                ctypes.windll.shell32.ShellExecuteW(
                    None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, self.TERMINAL_VISIBILITY
                )
            sys.exit()

    async def run_instance(self, channel_num: int, channel_id: str, start_delay: int, channel_tokens: list[str], time_limit_seconds: int):
        num_accounts = len(channel_tokens)
        self.DELAY = 30 * 60 / num_accounts  # Ideally 10 min delay per account (3 accounts)
        self.start_time = time.monotonic()
        await asyncio.sleep(start_delay)
        while True:
            for token in channel_tokens:
                if time.monotonic() - self.start_time >= time_limit_seconds:  # Time limit for automatic shutoff
                    print(f"\nℹ️ Time Limit Reached ℹ️\nChannel #{channel_num} has reached the time limit of {(time_limit_seconds / 60 / 60):.1f} hours. Stopping script in the channel...")
                    await self.send_message(token, self.tokens.index(token) + 1, channel_id, random.choice(self.TIME_LIMIT_EXCEEDED_MESSAGES), 0)
                    return
                print(f"\nChannel #{channel_num} - {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}")
                if self.DROP_SKIP_RATE < 0 or random.randint(1, self.DROP_SKIP_RATE) != 1:  # If SKIP_RATE == -1 (or any neg num), never skip
                    await self.drop_and_grab(token, self.tokens.index(token) + 1, channel_id, channel_tokens.copy())
                else:
                    print(f"✅ [Account #{self.tokens.index(token) + 1}] Skipped drop.")
                if self.DROP_FAIL_LIMIT >= 0 and drop_fail_count.value >= self.DROP_FAIL_LIMIT:  # If FAIL_LIMIT == -1 (or any neg num), never pause
                    input(f"\n⚠️ Drop Fail Limit Reached ⚠️\nThe script has failed to retrieve {self.DROP_FAIL_LIMIT} total drops. Automatically pausing script...\nPress `Enter` if you wish to resume.")
                    async with drop_fail_count_lock:
                        drop_fail_count.value = 0
                await asyncio.sleep(self.DELAY + random.uniform(0.5 * 60, 5 * 60))  # Wait an additional 0.5-5 minutes per drop

    async def run_script(self):
        if self.SHUFFLE_ACCOUNTS:
            self.shuffled_tokens = random.sample(self.tokens, len(self.tokens))
        else:
            self.shuffled_tokens = None

        await self.run_command_checker()
        await self.set_token_dictionaries()
        
        task_instances = []
        num_channels = len(self.DROP_CHANNEL_IDS)
        start_delay_multipliers = random.sample(range(num_channels), num_channels)
        for index, channel_id in enumerate(self.DROP_CHANNEL_IDS):
            channel_num = index + 1
            if self.CHANNEL_SKIP_RATE > 0 and random.randint(1, self.CHANNEL_SKIP_RATE) == 1:  # If SKIP_RATE == -1 (or any neg num), never skip
                print(f"\nℹ️ Channel #{channel_num} will be skipped.")
            else:
                channel_tokens = self.channel_token_dict[channel_id]
                start_delay_seconds = start_delay_multipliers[0] * 240 + random.uniform(5, 120)  # Randomly stagger start times
                start_delay_multipliers.pop(0)
                channel_time_limit_seconds = random.randint(self.TIME_LIMIT_HOURS_MIN * 60 * 60, self.TIME_LIMIT_HOURS_MAX * 60 * 60)  # Random time limit in seconds
                target_time = datetime.now() + timedelta(seconds = channel_time_limit_seconds)
                start_time = datetime.now() + timedelta(seconds = start_delay_seconds)
                print(f"\nℹ️ Channel #{channel_num} will run for {(channel_time_limit_seconds / 60 / 60):.1f} hrs (until {target_time.strftime('%I:%M %p').lstrip('0')}) " +
                        f"starting in {round(start_delay_seconds)}s ({start_time.strftime('%I:%M:%S %p').lstrip('0')}):")
                for token in channel_tokens:
                    print(f"  - Account #{self.tokens.index(token) + 1}")
                task_instances.append(asyncio.create_task(self.run_instance(channel_num, channel_id, start_delay_seconds, channel_tokens.copy(), channel_time_limit_seconds)))
        await asyncio.sleep(3)  # Short delay to show user the account/channel information
        await asyncio.gather(*task_instances)
        input("\n✅ Script Execution Completed ✅\nClose the terminal to exit, or press `Enter` to restart the script.")
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, self.TERMINAL_VISIBILITY
        )
        sys.exit()

if __name__ == "__main__":
    bot = MessageBotter()
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, bot.TERMINAL_VISIBILITY
        )
        sys.exit()
    bot.check_config()
    bot.tokens = TokenExtractor().main(len(bot.DROP_CHANNEL_IDS))
    drop_fail_count = DropFailCount(0)
    drop_fail_count_lock = asyncio.Lock()
    asyncio.run(bot.run_script())