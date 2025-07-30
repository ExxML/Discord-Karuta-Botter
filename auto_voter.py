import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import ctypes
import sys
import json
import time
import random

### TO USE THE AUTO-VOTER, YOU MUST HAVE A LIST OF TOKEN(S) in tokens.json. You cannot use account logins.
class AutoVoter():
    def __init__(self):
        try:
            with open("tokens.json", "r") as tokens_file:
                self.TOKENS = json.load(tokens_file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.TOKENS = []
        if not isinstance(self.TOKENS, list) or not all(isinstance(token, str) for token in self.TOKENS):
            input('⛔ Token Format Error ⛔\nExpected a list of strings. Example: ["token1", "token2", "token3"]')
            sys.exit()

        self.RAND_DELAY_MIN = 10  # (int) Minimum amount of MINUTES to wait between votes
        self.RAND_DELAY_MAX = 25 # (int) Maximum amount of MINUTES to wait between votes

        self.USER_AGENTS = [
            # Brave Browser - Windows 10/11
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.198 Safari/537.36 Brave/114.0.5735.198", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.170 Safari/537.36 Brave/115.0.5790.170", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.114 Safari/537.36 Brave/115.0.5790.114", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.111 Safari/537.36 Brave/116.0.5845.111", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.5845.97 Safari/537.36 Brave/116.0.5845.97", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.149 Safari/537.36 Brave/117.0.5938.149", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.132 Safari/537.36 Brave/117.0.5938.132", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.5938.62 Safari/537.36 Brave/117.0.5938.62", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.117 Safari/537.36 Brave/118.0.5993.117", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36 Brave/118.0.5993.90", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.88 Safari/537.36 Brave/118.0.5993.88", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.160 Safari/537.36 Brave/119.0.6045.160", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.123 Safari/537.36 Brave/119.0.6045.123", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.105 Safari/537.36 Brave/119.0.6045.105", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.224 Safari/537.36 Brave/120.0.6099.224", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.110 Safari/537.36 Brave/120.0.6099.110", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.72 Safari/537.36 Brave/120.0.6099.72", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.184 Safari/537.36 Brave/121.0.6167.184", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.139 Safari/537.36 Brave/121.0.6167.139", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36 Brave/121.0.6167.85", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.174 Safari/537.36 Brave/122.0.6261.174", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.128 Safari/537.36 Brave/122.0.6261.128", 
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.111 Safari/537.36 Brave/122.0.6261.111", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.95 Safari/537.36 Brave/122.0.6261.95", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.122 Safari/537.36 Brave/123.0.6312.122", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.106 Safari/537.36 Brave/123.0.6312.106", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.87 Safari/537.36 Brave/123.0.6312.87", 
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36 Brave/123.0.6312.86", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.207 Safari/537.36 Brave/124.0.6367.207", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.112 Safari/537.36 Brave/124.0.6367.112", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36 Brave/124.0.6367.91", 
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36 Brave/124.0.6367.91", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.113 Safari/537.36 Brave/125.0.6422.113", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.112 Safari/537.36 Brave/125.0.6422.112", 
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.76 Safari/537.36 Brave/125.0.6422.76", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.60 Safari/537.36 Brave/125.0.6422.60", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.127 Safari/537.36 Brave/126.0.6478.127", 
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.93 Safari/537.36 Brave/126.0.6478.93", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.61 Safari/537.36 Brave/126.0.6478.61", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.57 Safari/537.36 Brave/126.0.6478.57", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.112 Safari/537.36 Brave/127.0.6533.112", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.6533.77 Safari/537.36 Brave/127.0.6533.77"
        ]

    def load_chrome(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')  # Comment for non-headless mode if needed
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(f'--user-agent={random.choice(self.USER_AGENTS)}')
        
        self.driver = uc.Chrome(options = options, use_subprocess = True)

        # Webdriver spoofer
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        })

        # Spoof canvas
        canvas_script = """
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type, ...args) {
            const ctx = originalGetContext.call(this, type, ...args);
            if (type === '2d') {
                const originalGetImageData = ctx.getImageData;
                ctx.getImageData = function(x, y, w, h) {
                    const imageData = originalGetImageData.call(this, x, y, w, h);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] = imageData.data[i] ^ 1;
                    }
                    return imageData;
                }
            }
            return ctx;
        };
        """
        self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": canvas_script})

    def auto_vote(self, account_idx: int):
        try:
            # Navigate to Discord login
            self.driver.get("https://discord.com/login")
            WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
            print("  Opened Discord")

            inject_token_script = f"""
                let token = "{self.shuffled_tokens[account_idx]}";
                function login(token) {{
                    setInterval(() => {{
                        document.body.appendChild(document.createElement('iframe')).contentWindow.localStorage.token = `"${{token}}"`;
                    }}, 50);
                    setTimeout(() => {{
                        location.reload();
                    }}, 2500);
                }}
                login(token);
            """
            self.driver.execute_script(inject_token_script)
            print("  Injected token")

            # Wait for Discord to fully load
            WebDriverWait(self.driver, 15).until(lambda d: "/login" not in d.current_url)
            print("  Logged into Discord")
            time.sleep(2)  # Short delay to ensure Discord fully loads
            
            # Open top.gg
            self.driver.get("https://top.gg/bot/646937666251915264/vote")
            login_button = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Log')]")))
            login_button.click()
            print("  Opened Top.gg")

            # Wait for redirect to authorisation page
            WebDriverWait(self.driver, 15).until(lambda d: "/vote" not in d.current_url)
            print("  Redirected to authorisation page")
            
            # Authorise
            self.driver.get(self.driver.current_url)
            discord_authorize_button = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Auth')]")))
            discord_authorize_button.click()
            print("  Authorised Discord account- waiting 10s to vote...")

            # Wait 10s (watch ad to vote)
            time.sleep(10)

            # Vote
            vote_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Vote')]")))
            vote_button.click()
            time.sleep(1)  # Short delay to ensure vote is registered
            print("  ✅ Clicked vote button")
            self.driver.quit()

        except Exception as e:
            print(f"  ❌ Error with Acccount #{self.TOKENS.index(self.shuffled_tokens[account_idx]) + 1}:", e)
    
    def main(self):
        if self.TOKENS:
            self.shuffled_tokens = random.sample(self.TOKENS, len(self.TOKENS))
        else:
            input("⛔ Token Error ⛔\nNo tokens found. Please enter at least 1 token to vote with in tokens.json.")
            sys.exit()

        # Executes with tokens
        for account_idx in range(len(self.shuffled_tokens)):
            print(f"{datetime.now().strftime('%I:%M:%S %p').lstrip('0')}")
            print("Loading new undetected Chrome...")
            self.load_chrome()
            print(f"Auto-voting on Account #{self.TOKENS.index(self.shuffled_tokens[account_idx]) + 1} ({account_idx + 1}/{len(self.shuffled_tokens)})...")
            self.auto_vote(account_idx)
            print("Closing Chrome...")
            self.driver.quit()
            delay = random.uniform(self.RAND_DELAY_MIN, self.RAND_DELAY_MAX) * 60  # Random delay between votes
            print(f"Waiting {round(delay / 60)} minutes before voting again...\n")
            time.sleep(delay)

        input("✅ All accounts have been voted on. Press `Enter` to exit.")
        sys.exit()

if __name__ == "__main__":
    RELAUNCH_FLAG = "--no-relaunch"
    if RELAUNCH_FLAG not in sys.argv:
        ctypes.windll.shell32.ShellExecuteW(
            None, None, sys.executable, " ".join(sys.argv + [RELAUNCH_FLAG]), None, 1  # 0 = hidden, 1 = visible (recommended)
        )
        sys.exit()
    AutoVoter().main()