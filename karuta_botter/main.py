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
        # Enter your drop channels as a list of strings.
        self.DROP_CHANNEL_IDS = [
            "",
        ]
        # Enter your server activity drop channels as a list of strings (for reacting to drops with the special event emoji during Karuta events). 
        # Only used if self.SPECIAL_EVENT = True. Leave the list empty to disable grabbing the special event emoji on server activity based drops.
        self.SERVER_ACTIVITY_DROP_CHANNEL_IDS = [
            "",
        ]
        self.TERMINAL_VISIBILITY = 1  # 0 = hidden, 1 = visible (recommended)
        self.KARUTA_PREFIX = "k"  # (str) Karuta's bot prefix.
        self.SHUFFLE_ACCOUNTS = True  # (bool) Improve randomness by shuffling accounts across channels every time the script runs.
        self.RATE_LIMIT = 3  # (int) Maximum number of rate limits before giving up.
        self.DROP_FAIL_LIMIT = 3  # (int) Maximum number of failed drops across all channels before pausing script. Set to -1 if you wish to disable this limit.
        self.TIME_LIMIT_HOURS_MIN = 6  # (int/float) MINIMUM time limit in hours before script automatically pauses (to avoid ban risk).
        self.TIME_LIMIT_HOURS_MAX = 10  # (int/float) MAXIMUM time limit in hours before script automatically pauses (to avoid ban risk).
        self.CHANNEL_SKIP_RATE = 8  # (int) Every time the script runs, there is a 1/self.CHANNEL_SKIP_RATE chance of skipping a channel. Set to -1 if you wish to disable skipping.
        self.DROP_SKIP_RATE = 12  # (int) Every drop, there is a 1/self.DROP_SKIP_RATE chance of skipping the drop. Set to -1 if you wish to disable it skipping.
        self.RANDOM_COMMAND_RATE = 480  # (int) Every 2-3 seconds, there is a 1/self.RANDOM_COMMAND_RATE chance of sending a random command.
        self.SPECIAL_EVENT = False  # (bool) Whether the script will use the token in special_event_token.json to auto-react with the event emoji (if there is one) during Karuta special events.

        ### DO NOT MODIFY THESE CONSTANTS ###
        self.KARUTA_BOT_ID = "646937666251915264"  # Karuta's user ID
        self.KARUTA_DROP_MESSAGE = "is dropping 3 cards!"
        self.KARUTA_SERVER_ACTIVITY_DROP_MESSAGE = "I'm dropping 3 cards since this server is currently active!"
        self.KARUTA_EXPIRED_DROP_MESSAGE = "This drop has expired and the cards can no longer be grabbed."

        self.KARUTA_CARD_TRANSFER_TITLE = "Card Transfer"

        self.KARUTA_MULTITRADE_LOCK_MESSAGE = "Both sides must lock in before proceeding to the next step."
        self.KARUTA_MULTITRADE_CONFIRM_MESSAGE = "This trade has been locked."

        self.KARUTA_MULTIBURN_TITLE = "Burn Cards"

        self.RANDOM_ADDON = ['', ' ', ' !', ' :D', ' w']
        self.DROP_MESSAGES = [f"{self.KARUTA_PREFIX}drop", f"{self.KARUTA_PREFIX}d"]
        self.RANDOM_COMMANDS = [
            f"{self.KARUTA_PREFIX}reminders", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", 
            f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", 
            f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", 
            f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}rm", f"{self.KARUTA_PREFIX}lookup", 
            f"{self.KARUTA_PREFIX}lu", f"{self.KARUTA_PREFIX}vote", f"{self.KARUTA_PREFIX}view", 
            f"{self.KARUTA_PREFIX}v", f"{self.KARUTA_PREFIX}collection", f"{self.KARUTA_PREFIX}c", 
            f"{self.KARUTA_PREFIX}c o:wl", f"{self.KARUTA_PREFIX}c o:p", f"{self.KARUTA_PREFIX}c o:eff", 
            f"{self.KARUTA_PREFIX}cardinfo", f"{self.KARUTA_PREFIX}ci", f"{self.KARUTA_PREFIX}cd", 
            f"{self.KARUTA_PREFIX}cd", f"{self.KARUTA_PREFIX}cd", f"{self.KARUTA_PREFIX}cd", 
            f"{self.KARUTA_PREFIX}cooldowns", f"{self.KARUTA_PREFIX}daily", f"{self.KARUTA_PREFIX}monthly", 
            f"{self.KARUTA_PREFIX}help", f"{self.KARUTA_PREFIX}wishlist", f"{self.KARUTA_PREFIX}wl", 
            f"{self.KARUTA_PREFIX}jobboard", f"{self.KARUTA_PREFIX}jb", f"{self.KARUTA_PREFIX}shop", 
            f"{self.KARUTA_PREFIX}itemshop", f"{self.KARUTA_PREFIX}gemshop", f"{self.KARUTA_PREFIX}frameshop", 
            f"{self.KARUTA_PREFIX}inventory", f"{self.KARUTA_PREFIX}inv", f"{self.KARUTA_PREFIX}i", 
            f"{self.KARUTA_PREFIX}schedule", f"{self.KARUTA_PREFIX}blackmarket", f"{self.KARUTA_PREFIX}bm"
        ]
        self.RANDOM_MESSAGES = [
            "bruhh", "ggzz", "dude lmao", "tf what", "omg nice", "dam welp", "crazy stuf", "look at dis", "wowza", 
            "wait huh", "umm what", "heyy", "hellooo", "yo", "hows it goin", "thats insane", "nice card", "pretty", 
            "nice drop lol", "clean grab", "dannggg what I wanted that", "can I give u one of my cards for that", 
            "yo i need that card", "gimme that", "how long have you had that??", "check my inv lol", 
            "dude accept the trade", "where should i kmt u?", "ayoo that's clean", "no way you dropped that", 
            "i was just about to grab", "hold up fr?", "yo what are the odds", "someone always steals my pull 😭", 
            "BRO just got my dream card", "real lucky today huh", "wait how rare is that", "gg bro", "wait lemme check wiki", 
            "nah that's a flex card fr", "i swear my luck is cursed", "yo who boosting drops rn", "bruh that was mine 😤", 
            "bet you won't trade that", "wait lemme drop too", "someone check its value lol", "bro always grabs fast af", 
            "here kmt me", "who tryna kmt", "u online for trade?", "can i see ur favs?", "i swear it's rigged", 
            "dawg i was afk nooOO", "nah fr that's wild", "yo queue with me real quick", "yo why so many rares today", 
            "i swear u always pull good stuff", "damn stop stealing my luck lol", "wait that's mint condition right?", 
            "hold up is that sketch art?", "bruh where my luck at", "yo let's duel after this", "tryna 1v1 for it?", 
            "how tf u keep dropping bangers", "wait i missed it BRUH", "i got scammed in trade lol"
            "yo i blinked and missed it", "how u pull sm heat", "who boosting rn lol", "lemme borrow ur luck", 
            "stoppp that's too clean", "yo fr stop hoggin", "wait that's signed right?", "please trade it to me", 
            "you farming rn?", "yo gimme that theme", "bruh stop stealing drops", "i swear that was mine", 
            "how's that even possible lol", "yo ggs on that pull", "can't believe u got that", "W pull fr", 
            "yo thats actually cracked", "nah you cheating fr", "how that even drop here", "yo can i see ur binder", 
            "is that a foil??", "yo whered u get that bg", "nahhh that card's nuts", "WISHING WORKED OMG", 
            "no shot you got that", "how do u drop so good", "yo that pull's fire", "stop flexin ur pulls 🥺", 
            "wait what event is this from", "yo i'm savin that pull", "yo i need to start wishing", "gimme that plsss", 
            "is that even tradable?", "i swear u got admin luck", "yo queue with me bruh", "that card go hard", 
            "lemme wishlist that real quick", "whyd u drop in this channel", "yo teach me your luck", 
            "i'll trade u 3 for it fr", "you pull like a whale", "yo check auction prices", "nah im done lmao", 
            "yo queue now or i'm stealing", "why so many good cards today", "i got baited smh", "yo that's a set piece?", 
            "wait was that a dupe?", "i need that in my favs", "nah u got god luck today", "yo stop sniping me", 
            "i was lagging bruh", "pleaseeee i'll overpay", "yo is that new art?"
        ]
        self.EMOJIS = ['1️⃣', '2️⃣', '3️⃣']
        self.EMOJI_MAP = {
            '1️⃣': '[1]',
            '2️⃣': '[2]',
            '3️⃣': '[3]'
        }

        self.TIME_LIMIT_EXCEEDED_MESSAGES = ["stawp", "stoop", "quittin", "q", "exeeting", "exité", "ceeze", "cloze", '🛑', '🚫', '❌', '⛔']

        self.pause_event = asyncio.Event()
        self.pause_event.set()
        self.DROP_FAIL_LIMIT_REACHED_FLAG = "Drop Fail Limit Reached"
        self.EXECUTION_COMPLETED_FLAG = "Execution Completed"

        self.WINDOWS_VERSIONS = ["10.0", "11.0"]
        self.BROWSER_VERSIONS = [
            "114.0.5735.198", "115.0.5790.170", "115.0.5790.114", "116.0.5845.111", 
            "116.0.5845.97", "117.0.5938.149", "117.0.5938.132", "117.0.5938.62", 
            "118.0.5993.117", "118.0.5993.90", "118.0.5993.88", "119.0.6045.160", 
            "119.0.6045.123", "119.0.6045.105", "120.0.6099.224", "120.0.6099.110", 
            "120.0.6099.72", "121.0.6167.184", "121.0.6167.139", "121.0.6167.85", 
            "122.0.6261.174", "122.0.6261.128", "122.0.6261.111", "122.0.6261.95", 
            "123.0.6312.122", "123.0.6312.106", "123.0.6312.87", "123.0.6312.86", 
            "124.0.6367.207", "124.0.6367.112", "124.0.6367.91", "124.0.6367.91", 
            "125.0.6422.113", "125.0.6422.112", "125.0.6422.76", "125.0.6422.60", 
            "126.0.6478.127", "126.0.6478.93", "126.0.6478.61", "126.0.6478.57", 
            "127.0.6533.112", "127.0.6533.77"
        ]

        # Set up variables
        self.drop_fail_count = 0
        self.drop_fail_count_lock = asyncio.Lock()
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
                all(id.isdigit() for id in self.SERVER_ACTIVITY_DROP_CHANNEL_IDS),
                self.KARUTA_BOT_ID.isdigit()
            ]):
                input("⛔ Configuration Error ⛔\nPlease enter non-empty, numeric strings for the command user ID(s), command server/channel ID, (server activity) drop channel ID(s), and Karuta bot ID in main.py.")
                sys.exit()
        except AttributeError:
            input("⛔ Configuration Error ⛔\nPlease enter strings (not integers) for the command user ID(s), command server/channel ID, (server activity) drop channel ID(s), and Karuta bot ID in main.py.")
            sys.exit()
        if not all([
            isinstance(self.TERMINAL_VISIBILITY, int),
            isinstance(self.KARUTA_PREFIX, str),
            isinstance(self.SHUFFLE_ACCOUNTS, bool),
            isinstance(self.RATE_LIMIT, int),
            isinstance(self.DROP_FAIL_LIMIT, int),
            isinstance(self.TIME_LIMIT_HOURS_MIN, (int, float)),
            isinstance(self.TIME_LIMIT_HOURS_MAX, (int, float)),
            isinstance(self.CHANNEL_SKIP_RATE, int),
            isinstance(self.DROP_SKIP_RATE, int),
            isinstance(self.RANDOM_COMMAND_RATE, int),
            isinstance(self.SPECIAL_EVENT, bool),
            self.TERMINAL_VISIBILITY in (0, 1),
            self.RATE_LIMIT >= 0,
            self.TIME_LIMIT_HOURS_MIN >= 0,
            self.TIME_LIMIT_HOURS_MAX >= 0,
            self.CHANNEL_SKIP_RATE != 0,
            self.DROP_SKIP_RATE != 0,
            self.RANDOM_COMMAND_RATE > 0
        ]):
            input("⛔ Configuration Error ⛔\nPlease enter valid constant values in main.py.")
            sys.exit()
        if self.TIME_LIMIT_HOURS_MIN > self.TIME_LIMIT_HOURS_MAX:
            input("⛔ Configuration Error ⛔\nPlease enter a maximum time limit greater than the minimum time limit in main.py.")
            sys.exit()

    def get_headers(self, token: str, channel_id: str):
        if token not in self.token_headers:
            windows_version = random.choice(self.WINDOWS_VERSIONS)
            browser_version = random.choice(self.BROWSER_VERSIONS)
            build_number = random.choice([381653, 382032, 382201, 382355, 417521])  # Random Discord build version numbers
            super_properties = {
                "os": "Windows",
                "browser": "Chrome",
                "device": "",
                "system_locale": "en-US",
                "browser_user_agent": (
                    f"Mozilla/5.0 (Windows NT {windows_version}; Win64; x64) "
                    f"AppleWebKit/537.36 (KHTML, like Gecko) "
                    f"Chrome/{browser_version} Safari/537.36 Brave/{browser_version}"  # Brave Browser - Windows 10/11 (Brave bypasses most Cloudflare detections)
                ),
                "browser_version": browser_version,
                "os_version": windows_version.split(".")[0],  # Ex. 10.0 -> 10
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
                    "location_channel_id": channel_id,
                    "location_channel_type": 1,
                }).encode()).decode()
            }
        return self.token_headers[token]

    async def get_drop_message(self, token: str, account: int, channel_id: str, wait_for_emoji: bool):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=5"
        headers = self.get_headers(token, channel_id)
        timeout = 30  # seconds
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            while (time.monotonic() - start_time) < timeout:
                async with session.get(url, headers = headers) as resp:
                    status = resp.status
                    if status == 200:
                        messages = await resp.json()
                        for msg in messages:
                            reactions = msg.get('reactions', [])
                            if all([
                                msg.get('author', {}).get('id') == self.KARUTA_BOT_ID,
                                len(reactions) >= 3,
                                self.KARUTA_DROP_MESSAGE in msg.get('content', ''),
                                self.KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', '')
                            ]):
                                if self.SPECIAL_EVENT and wait_for_emoji:  # If special event, wait an additional 2-3s to watch for the special event emoji
                                    await asyncio.sleep(random.uniform(2, 3))
                                    wait_for_emoji = False
                                    continue
                                print(f"✅ [Account #{account}] Retrieved drop message.")
                                return msg
                        if not wait_for_emoji:
                            continue
                    elif status == 401:
                        print(f"❌ [Account #{account}] Retrieve drop message failed ({self.drop_fail_count + 1}/{self.DROP_FAIL_LIMIT}): Invalid token.")
                        async with self.drop_fail_count_lock:
                            self.drop_fail_count += 1
                        return None
                    elif status == 403:
                        print(f"❌ [Account #{account}] Retrieve drop message failed ({self.drop_fail_count + 1}/{self.DROP_FAIL_LIMIT}): Token banned or insufficient permissions.")
                        async with self.drop_fail_count_lock:
                            self.drop_fail_count += 1
                        return None
                await asyncio.sleep(random.uniform(0.5, 1))
            print(f"❌ [Account #{account}] Retrieve drop message failed ({self.drop_fail_count + 1}/{self.DROP_FAIL_LIMIT}): Timed out ({timeout}s).")
            async with self.drop_fail_count_lock:
                self.drop_fail_count += 1
            return None

    async def send_message(self, token: str, account: int, channel_id: str, content: str, rate_limited: int):
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        headers = self.get_headers(token, channel_id)
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
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=50"
        headers = self.get_headers(token, channel_id)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers = headers) as resp:
                status = resp.status
                if status == 200:
                    messages = await resp.json()
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
                elif status == 429 and rate_limited < self.RATE_LIMIT:
                    rate_limited += 1
                    retry_after = 1  # seconds
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
        headers = self.get_headers(token, channel_id)
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers = headers) as resp:
                status = resp.status
                if emoji in self.EMOJIS:
                    card_number = self.EMOJI_MAP.get(emoji)
                    if status == 204:
                        print(f"✅ [Account #{account}] Grabbed card {card_number}.")
                    elif status == 401:
                        print(f"❌ [Account #{account}] Grab card {card_number} failed: Invalid token.")
                    elif status == 403:
                        print(f"❌ [Account #{account}] Grab card {card_number} failed: Token banned or insufficient permissions.")
                    elif status == 429 and rate_limited < self.RATE_LIMIT:
                        rate_limited += 1
                        retry_after = 1  # seconds
                        print(f"⚠️ [Account #{account}] Grab card {card_number} failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                        await asyncio.sleep(retry_after)
                        await self.add_reaction(token, account, channel_id, message_id, emoji, rate_limited)
                    else:
                        print(f"❌ [Account #{account}] Grab card {card_number} failed: Error code {status}.")
                elif account == 0 and self.SPECIAL_EVENT and self.special_event_token:  # when reacting for special event emoji
                    if status == 204:
                        print(f"✅ [Special Event Account] Reacted {emoji}.")
                    elif status == 401:
                        print(f"❌ [Special Event Account] React {emoji} failed: Invalid token.")
                    elif status == 403:
                        print(f"❌ [Special Event Account] React {emoji} failed: Token banned or insufficient permissions.")
                    elif status == 429 and rate_limited < self.RATE_LIMIT:
                        rate_limited += 1
                        retry_after = 1  # seconds
                        print(f"⚠️ [Special Event Account] React {emoji} failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                        await asyncio.sleep(retry_after)
                        await self.add_reaction(token, account, channel_id, message_id, emoji, rate_limited)
                    else:
                        print(f"❌ [Special Event Account] React {emoji} failed: Error code {status}.")
                else:  # when manually reacting with message commands
                    if status == 204:
                        print(f"✅ [Account #{account}] Reacted {emoji}.")
                    elif status == 401:
                        print(f"❌ [Account #{account}] React {emoji} failed: Invalid token.")
                    elif status == 403:
                        print(f"❌ [Account #{account}] React {emoji} failed: Token banned or insufficient permissions.")
                    elif status == 429 and rate_limited < self.RATE_LIMIT:
                        rate_limited += 1
                        retry_after = 1  # seconds
                        print(f"⚠️ [Account #{account}] React {emoji} failed ({rate_limited}/{self.RATE_LIMIT}): Rate limited, retrying after {retry_after}s.")
                        await asyncio.sleep(retry_after)
                        await self.add_reaction(token, account, channel_id, message_id, emoji, rate_limited)
                    else:
                        print(f"❌ [Account #{account}] React {emoji} failed: Error code {status}.")

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

    async def run_special_event_checker(self):
        while True:
            try:
                for server_activity_drop_channel_id in self.SERVER_ACTIVITY_DROP_CHANNEL_IDS:
                    url = f"https://discord.com/api/v10/channels/{server_activity_drop_channel_id}/messages?limit=20"
                    headers = self.get_headers(self.special_event_token, server_activity_drop_channel_id)
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers = headers) as resp:
                            status = resp.status
                            if status == 200:
                                messages = await resp.json()
                                try:
                                    for msg in messages:
                                        if all([
                                            msg.get('author', {}).get('id') == self.KARUTA_BOT_ID,
                                            len(msg.get('reactions', [])) > 3,  # 3 cards + 1 special event emoji
                                            msg.get('reactions', []) and msg.get('reactions', [])[-1].get('count') == 1,  # ensure there is only 1 reaction (Karuta's) on the special event emoji
                                            (self.KARUTA_DROP_MESSAGE in msg.get('content', '') or self.KARUTA_SERVER_ACTIVITY_DROP_MESSAGE in msg.get('content', '')),
                                            self.KARUTA_EXPIRED_DROP_MESSAGE not in msg.get('content', '')
                                        ]):
                                            special_event_emoji = msg.get('reactions', [])[-1].get('emoji').get('name')  # Get the last (4th) emoji (the event emoji)
                                            await self.add_reaction(self.special_event_token, 0, server_activity_drop_channel_id, msg.get('id'), special_event_emoji, 0)  # 0 as account_num stub
                                except IndexError:
                                    pass
                            else:
                                print(f"❌ [Special Event Account] Retrieve message failed: Error code {status}.")
                                return None
            except Exception:
                await asyncio.sleep(5)
                pass
            await asyncio.sleep(2)  # Short delay between checking channels to avoid rate-limiting

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
            drop_message = await self.get_drop_message(token, account, channel_id, wait_for_emoji = True)
            if drop_message:
                drop_message_id = drop_message.get('id')
                random.shuffle(self.EMOJIS)  # Shuffle emojis for random emoji order
                random.shuffle(channel_tokens)  # Shuffle tokens for random emoji assignment
                for i in range(num_channel_tokens):
                    emoji = self.EMOJIS[i]
                    grab_token = channel_tokens[i]
                    grab_account = self.tokens.index(grab_token) + 1
                    await self.add_reaction(grab_token, grab_account, channel_id, drop_message_id, emoji, 0)
                    await asyncio.sleep(random.uniform(0.5, 3.5))
                try:
                    if self.SPECIAL_EVENT and self.special_event_token and len(drop_message.get('reactions', [])) > 3:  # 3 cards + 1 special event emoji
                        await asyncio.sleep(random.uniform(0, 3))
                        special_event_emoji = drop_message.get('reactions', [])[-1].get('emoji').get('name')  # Get the last (4th) emoji (the event emoji)
                        await self.add_reaction(self.special_event_token, 0, channel_id, drop_message_id, special_event_emoji, 0)  # 0 as account_num stub
                except IndexError:
                    pass
                random.shuffle(channel_tokens)  # Shuffle tokens again for random order messages
                for i in range(num_channel_tokens):
                    if random.choice([True, False]):  # 50% chance of sending messages
                        grab_token = channel_tokens[i]
                        grab_account = self.tokens.index(grab_token) + 1
                        for _ in range(random.randint(1, 3)):
                            random_msg_list = random.choice([self.RANDOM_COMMANDS, self.RANDOM_MESSAGES])
                            random_message = random.choice(random_msg_list)
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

    async def async_input_handler(self, prompt: str, target_command: str, flag: str):
        while True:
            if self.pause_event.is_set():
                self.pause_event.clear()  # Pause drops, but not commands
            command = await asyncio.to_thread(input, prompt)
            if command == target_command:  # Resume if target command is inputted
                if flag == self.DROP_FAIL_LIMIT_REACHED_FLAG and self.DROP_FAIL_LIMIT >= 0 and self.drop_fail_count >= self.DROP_FAIL_LIMIT:
                    async with self.drop_fail_count_lock:
                        self.drop_fail_count = 0
                    print("\nℹ️ Reset drop fail count. Resuming drops...")
                elif flag == self.EXECUTION_COMPLETED_FLAG:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, self.TERMINAL_VISIBILITY
                    )
                    sys.exit()
                self.pause_event.set()
                break  # Continue the script

    async def run_instance(self, channel_num: int, channel_id: str, start_delay: int, channel_tokens: list[str], time_limit_seconds: int):
        try:
            num_accounts = len(channel_tokens)
            self.DELAY = 30 * 60 / num_accounts  # Ideally 10 min delay per account (3 accounts)
            # Breaking up start delay into multiple steps to check if need to pause
            random_start_delay_per_step = random.uniform(2, 3)
            num_start_delay_steps = round(start_delay / random_start_delay_per_step)
            for _ in range(num_start_delay_steps):
                await self.pause_event.wait()  # Check if need to pause
                await asyncio.sleep(random_start_delay_per_step)
            self.start_time = time.monotonic()
            while True:
                for token in channel_tokens:
                    print(f"\nChannel #{channel_num} - {datetime.now().strftime('%I:%M:%S %p').lstrip('0')}")
                    if time.monotonic() - self.start_time >= time_limit_seconds:  # Time limit for automatic shutoff
                        print(f"ℹ️ Channel #{channel_num} has reached the time limit of {(time_limit_seconds / 60 / 60):.1f} hours. Stopping script in channel...")
                        await self.send_message(token, self.tokens.index(token) + 1, channel_id, random.choice(self.TIME_LIMIT_EXCEEDED_MESSAGES), 0)
                        return
                    if self.DROP_SKIP_RATE < 0 or random.randint(1, self.DROP_SKIP_RATE) != 1:  # If SKIP_RATE == -1 (or any neg num), never skip
                        await self.drop_and_grab(token, self.tokens.index(token) + 1, channel_id, channel_tokens.copy())
                    else:
                        print(f"✅ [Account #{self.tokens.index(token) + 1}] Skipped drop.")
                    await self.pause_event.wait()  # Check if need to pause
                    if self.DROP_FAIL_LIMIT >= 0 and self.drop_fail_count >= self.DROP_FAIL_LIMIT:  # If FAIL_LIMIT == -1 (or any neg num), never pause
                        if self.COMMAND_SERVER_ID and self.COMMAND_CHANNEL_ID:
                            await self.send_message(token, self.tokens.index(token) + 1, self.COMMAND_CHANNEL_ID, "⚠️ Drop fail limit reached", 0)
                        if self.TERMINAL_VISIBILITY:
                            await self.async_input_handler(f"\n⚠️ Drop Fail Limit Reached ⚠️\nThe script has failed to retrieve {self.DROP_FAIL_LIMIT} total drops. Automatically pausing script...\nPress `Enter` if you wish to resume.",
                                                                            "", self.DROP_FAIL_LIMIT_REACHED_FLAG)
                    # Breaking up delay into multiple steps to check if need to pause
                    random_delay = self.DELAY + random.uniform(0.5 * 60, 5 * 60)  # Wait an additional 0.5-5 minutes per drop
                    random_delay_per_step = random.uniform(2, 3)
                    num_delay_steps = round(random_delay / random_delay_per_step)
                    for _ in range(num_delay_steps):
                        await self.pause_event.wait()  # Check if need to pause
                        await asyncio.sleep(random_delay_per_step)
                        if random.randint(1, self.RANDOM_COMMAND_RATE) == 1:
                            await self.send_message(token, self.tokens.index(token) + 1, channel_id, random.choice(self.RANDOM_COMMANDS), 0)
        except Exception as e:
            print(f"\n❌ Error in Channel Instance #{channel_num} ❌\n{e}")

    async def run_script(self):
        if self.SHUFFLE_ACCOUNTS:
            self.shuffled_tokens = random.sample(self.tokens, len(self.tokens))
        else:
            self.shuffled_tokens = None

        await self.run_command_checker()
        await self.set_token_dictionaries()
        
        if self.SPECIAL_EVENT:
            try:
                with open("special_event_token.json", "r") as special_event_token_file:
                    self.special_event_token = json.load(special_event_token_file)
                    if not isinstance(self.special_event_token, str):
                        input('⛔ Special Event Token Error ⛔\nExpected a string. Example: "token1"')
                        sys.exit()
                    elif self.special_event_token == "":
                        print("\n❌ Not watching for special event reactions (no token entered in special_event_token.json).")
                    else:
                        asyncio.create_task(self.run_special_event_checker())
                        print(f"\nℹ️ Watching for special event reactions in script drop channels + {len(self.SERVER_ACTIVITY_DROP_CHANNEL_IDS)} server activity drop channel(s).")
            except FileNotFoundError:
                self.special_event_token = ""
                print("\n❌ Not watching for special event reactions (no special_event_token.json file found).")
            except json.JSONDecodeError:
                input('⛔ Special Event Token Error ⛔\nExpected a string. Example: "token1"')
                sys.exit()
        else:
            self.special_event_token = ""

        task_instances = []
        num_channels = len(self.DROP_CHANNEL_IDS)
        start_delay_multipliers = random.sample(range(num_channels), num_channels)
        for index, channel_id in enumerate(self.DROP_CHANNEL_IDS):
            channel_num = index + 1
            if self.CHANNEL_SKIP_RATE > 0 and random.randint(1, self.CHANNEL_SKIP_RATE) == 1:  # If SKIP_RATE == -1 (or any neg num), never skip
                print(f"\nℹ️ Channel #{channel_num} will be skipped.")
            else:
                channel_tokens = self.channel_token_dict[channel_id]
                start_delay_seconds = start_delay_multipliers[0] * 210 + random.uniform(5, 60)  # Randomly stagger start times
                start_delay_multipliers.pop(0)
                channel_time_limit_seconds = round(random.uniform(self.TIME_LIMIT_HOURS_MIN * 60 * 60, self.TIME_LIMIT_HOURS_MAX * 60 * 60))  # Random time limit in seconds
                target_time = datetime.now() + timedelta(seconds = start_delay_seconds) + timedelta(seconds = channel_time_limit_seconds)
                start_time = datetime.now() + timedelta(seconds = start_delay_seconds)
                print(f"\nℹ️ Channel #{channel_num} will run for {(channel_time_limit_seconds / 60 / 60):.1f} hrs (until {target_time.strftime('%I:%M %p').lstrip('0')}) " +
                        f"starting in {round(start_delay_seconds)}s ({start_time.strftime('%I:%M:%S %p').lstrip('0')}):")
                for token in channel_tokens:
                    print(f"  - Account #{self.tokens.index(token) + 1}")
                task_instances.append(asyncio.create_task(self.run_instance(channel_num, channel_id, start_delay_seconds, channel_tokens.copy(), channel_time_limit_seconds)))
        await asyncio.sleep(3)  # Short delay to show user the account/channel information
        await asyncio.gather(*task_instances)
        await asyncio.sleep(1)
        if self.COMMAND_SERVER_ID and self.COMMAND_CHANNEL_ID:
            random_token = random.choice(self.tokens)
            await self.send_message(random_token, self.tokens.index(random_token) + 1, self.COMMAND_CHANNEL_ID, "✅ Execution completed", 0)
        if self.TERMINAL_VISIBILITY:
            await self.async_input_handler(f"\n✅ Script Execution Completed ✅\nClose the terminal to exit, or press `Enter` to restart the script.", "", self.EXECUTION_COMPLETED_FLAG)

if __name__ == "__main__":
    bot = MessageBotter()
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, bot.TERMINAL_VISIBILITY
        )
        sys.exit()
    bot.check_config()
    bot.tokens = TokenExtractor().main(len(bot.DROP_CHANNEL_IDS), bot.WINDOWS_VERSIONS, bot.BROWSER_VERSIONS)
    asyncio.run(bot.run_script())