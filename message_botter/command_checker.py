import aiohttp
import asyncio
import random
import uuid

class CommandChecker():
    def __init__(self, main, tokens, server_id, channel_id, karuta_prefix, karuta_bot_id, karuta_drop_message, karuta_expired_drop_message, 
                      karuta_card_transfer_title, karuta_multitrade_lock_message, karuta_multitrade_confirm_message, karuta_multiburn_title, rate_limit):
        self.main = main
        self.tokens = tokens
        self.SERVER_ID = server_id
        self.CHANNEL_ID = channel_id
        self.KARUTA_PREFIX = karuta_prefix
        self.KARUTA_BOT_ID = karuta_bot_id
        self.KARUTA_DROP_MESSAGE = karuta_drop_message
        self.KARUTA_EXPIRED_DROP_MESSAGE = karuta_expired_drop_message
        self.KARUTA_CARD_TRANSFER_TITLE = karuta_card_transfer_title
        self.KARUTA_MULTITRADE_LOCK_MESSAGE = karuta_multitrade_lock_message
        self.KARUTA_MULTITRADE_CONFIRM_MESSAGE = karuta_multitrade_confirm_message
        self.KARUTA_MULTIBURN_TITLE = karuta_multiburn_title
        self.RATE_LIMIT = rate_limit

        self.MESSAGE_COMMAND_PREFIX = "{cmd}"
        self.ALL_ACCOUNT_FLAG = "all"
        self.INTERACTION_URL = "https://discord.com/api/v10/interactions"
        self.KARUTA_LOCK_COMMAND = "{lock}"
        self.KARUTA_MULTIBURN_COMMAND = "{burn}"

        self.executed_commands = []
        self.card_transfer_messages = []
        self.multitrade_messages = []
        self.multiburn_initial_messages = []
        self.multiburn_fire_messages = []

    async def check_command(self, token: str):
        url = f"https://discord.com/api/v10/channels/{self.CHANNEL_ID}/messages?limit=3"
        headers = self.main.get_headers(token)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers = headers) as resp:
                status = resp.status
                if status == 200:
                    messages = await resp.json()
                    for msg in messages:
                        try:
                            raw_content = msg.get('content', '')
                            if raw_content.startswith(self.MESSAGE_COMMAND_PREFIX) and msg not in self.executed_commands:
                                self.executed_commands.append(msg)
                                content = raw_content.removeprefix(self.MESSAGE_COMMAND_PREFIX).strip()
                                account_str, command = content.split(" ", 1)
                                if account_str.isdigit():
                                    account = int(account_str)
                                    if account < 1 or account > len(self.tokens):
                                        print(f"❌ Error parsing command: Account number is not between 1 and {len(self.tokens)}.")
                                        return None, None, None
                                elif account_str.lower() == self.ALL_ACCOUNT_FLAG:
                                    account = self.ALL_ACCOUNT_FLAG
                                else:
                                    print("❌ Error parsing command: Account number is not a number or 'all'.")
                                    return None, None, None
                                if (command.startswith(f"{self.KARUTA_PREFIX}give") or command.startswith(f"{self.KARUTA_PREFIX}g")) and isinstance(account, int):
                                    print(f"🤖 Sending card transfer from Account #{account}...")
                                    send = True
                                elif command == self.KARUTA_LOCK_COMMAND and isinstance(account, int):
                                    print(f"🤖 Locking and confirming trade from Account #{account}...")
                                    send = False
                                elif (command.startswith(f"{self.KARUTA_PREFIX}multiburn") or command.startswith(f"{self.KARUTA_PREFIX}mb")) and isinstance(account, int):
                                    print(f"🤖 Multiburning on Account #{account}...")
                                    send = True
                                elif command == self.KARUTA_MULTIBURN_COMMAND and isinstance(account, int):
                                    print(f"🤖 Confirming multiburn on Account #{account}...")
                                    send = False
                                else:
                                    print(f"🤖 Sending '{command}' from {f'Account #{account}' if isinstance(account, int) else 'all accounts'}...")
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

    async def find_button(self, account: int, emoji: str, message: dict):
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
                            "guild_id": self.SERVER_ID,
                            "channel_id": self.CHANNEL_ID,
                            "message_flags": 0,
                            "message_id": message.get('id'),
                            "application_id": self.KARUTA_BOT_ID,
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

    async def check_card_transfer(self, token: str, account: int, command: str):
        if command.startswith(f"{self.KARUTA_PREFIX}give") or command.startswith(f"{self.KARUTA_PREFIX}g"):
            await asyncio.sleep(random.uniform(3, 6))  # Wait for Karuta card transfer message
            card_transfer_message = await self.main.get_karuta_message(token, account, self.KARUTA_CARD_TRANSFER_TITLE, self.RATE_LIMIT)
            if card_transfer_message and card_transfer_message not in self.card_transfer_messages:
                self.card_transfer_messages.append(card_transfer_message)
                # Find ✅ button
                payload = await self.find_button(account, '✅', card_transfer_message)
                if payload is not None:
                    async with aiohttp.ClientSession() as session:
                        headers = self.main.get_headers(token)
                        async with session.post(self.INTERACTION_URL, headers = headers, json = payload) as resp:
                            status = resp.status
                            if status == 204:
                                print(f"✅ [Account #{account}] Confirmed card transfer.")
                            else:
                                print(f"❌ [Account #{account}] Confirm card transfer failed: Error code {status}.")

    async def check_multitrade(self, token: str, account: int, command: str):
        if command == self.KARUTA_LOCK_COMMAND:
            multitrade_lock_message = await self.main.get_karuta_message(token, account, self.KARUTA_MULTITRADE_LOCK_MESSAGE, self.RATE_LIMIT)
            if multitrade_lock_message and multitrade_lock_message not in self.multitrade_messages:
                self.multitrade_messages.append(multitrade_lock_message)
                # Find 🔒 button
                lock_payload = await self.find_button(account, '🔒', multitrade_lock_message)
                if lock_payload is not None:
                    async with aiohttp.ClientSession() as session:
                        headers = self.main.get_headers(token)
                        async with session.post(self.INTERACTION_URL, headers = headers, json = lock_payload) as lock_resp:
                            status = lock_resp.status
                            if status == 204:
                                print(f"✅ [Account #{account}] Locked multitrade.")
                                await asyncio.sleep(random.uniform(3, 6))  # Wait for Karuta multitrade message to update
                                multitrade_confirm_message = await self.main.get_karuta_message(token, account, self.KARUTA_MULTITRADE_CONFIRM_MESSAGE, self.RATE_LIMIT)
                                # Find ✅ button
                                check_payload = await self.find_button(account, '✅', multitrade_confirm_message)
                                if check_payload is not None:
                                    async with session.post(self.INTERACTION_URL, headers = headers, json = check_payload) as check_resp:
                                        status = check_resp.status
                                        if status == 204:
                                            print(f"✅ [Account #{account}] Confirmed multitrade.")
                                        else:
                                            print(f"❌ [Account #{account}] Confirm multitrade failed: Error code {status}.")
                            else:
                                print(f"❌ [Account #{account}] Lock multitrade failed: Error code {status}.")

    async def check_multiburn(self, token: str, account: int, command: str):
        if command.startswith(f"{self.KARUTA_PREFIX}multiburn") or command.startswith(f"{self.KARUTA_PREFIX}mb"):
            await asyncio.sleep(random.uniform(3, 6))  # Wait for Karuta multiburn message
            multiburn_initial_message = await self.main.get_karuta_message(token, account, self.KARUTA_MULTIBURN_TITLE, self.RATE_LIMIT)
            if multiburn_initial_message and multiburn_initial_message not in self.multiburn_initial_messages:
                await asyncio.sleep(3)  # Longer delay to wait for check button to enable
                self.multiburn_initial_messages.append(multiburn_initial_message)
                # Find ☑️ button
                payload = await self.find_button(account, '☑️', multiburn_initial_message)
                if payload is not None:
                    async with aiohttp.ClientSession() as session:
                        headers = self.main.get_headers(token)
                        async with session.post(self.INTERACTION_URL, headers = headers, json = payload) as resp:
                            status = resp.status
                            if status == 204:
                                print(f"✅ [Account #{account}] Confirmed initial (0/2) multiburn.")
                            else:
                                print(f"❌ [Account #{account}] Confirm initial (0/2) multiburn failed: Error code {status}.")

    async def confirm_multiburn(self, token: str, account: int, command: str):
        if command == self.KARUTA_MULTIBURN_COMMAND:
            multiburn_fire_message = await self.main.get_karuta_message(token, account, self.KARUTA_MULTIBURN_TITLE, self.RATE_LIMIT)
            if multiburn_fire_message and multiburn_fire_message not in self.multiburn_fire_messages:
                self.multiburn_fire_messages.append(multiburn_fire_message)
                # Find 🔥 button
                fire_payload = await self.find_button(account, '🔥', multiburn_fire_message)
                if fire_payload is not None:
                    async with aiohttp.ClientSession() as session:
                        headers = self.main.get_headers(token)
                        async with session.post(self.INTERACTION_URL, headers = headers, json = fire_payload) as fire_resp:
                            status = fire_resp.status
                            if status == 204:
                                print(f"✅ [Account #{account}] Confirmed initial (1/2) multiburn.")
                                await asyncio.sleep(random.uniform(3, 6))  # Wait for Karuta multiburn message to update
                                multiburn_confirm_message = await self.main.get_karuta_message(token, account, self.KARUTA_MULTIBURN_TITLE, self.RATE_LIMIT)
                                # Find ✅ button
                                check_payload = await self.find_button(account, '✅', multiburn_confirm_message)
                                if check_payload is not None:
                                    async with session.post(self.INTERACTION_URL, headers = headers, json =check_payload) as check_resp:
                                        status = check_resp.status
                                        if status == 204:
                                            print(f"✅ [Account #{account}] Confirmed final (2/2) multiburn.")
                                        else:
                                            print(f"❌ [Account #{account}] Confirm final (2/2) multiburn failed: Error code {status}.")
                            else:
                                print(f"❌ [Account #{account}] Confirm initial (1/2) multiburn failed: Error code {status}.")

    async def run(self):
        while True:
            send, account, command = await self.check_command(random.choice(self.tokens))  # Use a random account to check for message commands
            if account and command:
                if account == self.ALL_ACCOUNT_FLAG:
                    for index, token in enumerate(self.tokens):
                        account = index + 1
                        await self.main.send_message(token, account, command, self.RATE_LIMIT)  # Won't retry even if rate-limited (so it doesn't interfere with drops/grabs)
                        await asyncio.sleep(random.uniform(1, 2))
                else:
                    token = self.tokens[account - 1]
                    if send:
                        await self.main.send_message(token, account, command, self.RATE_LIMIT)
                    await self.check_card_transfer(token, account, command)
                    await self.check_multitrade(token, account, command)
                    await self.check_multiburn(token, account, command)
                    await self.confirm_multiburn(token, account, command)
                print("🤖 Message command executed.")
            await asyncio.sleep(random.uniform(2, 5))  # Short delay to avoid getting rate-limited