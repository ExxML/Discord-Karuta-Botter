import aiohttp
import asyncio

tokens = [
    "token1",
    "token2",
    # Add more tokens
]

channel_id = "123456789012345678"  # Target channel

async def send_message(token, content):
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    json = {"content": content}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=json) as resp:
            print(f"{token[:5]}...: {resp.status}")
            if resp.status != 200 and resp.status != 201:
                print(await resp.text())

async def main():
    tasks = []
    for i, token in enumerate(tokens):
        tasks.append(send_message(token, f"Hello from account #{i+1}!"))
    await asyncio.gather(*tasks)

asyncio.run(main())