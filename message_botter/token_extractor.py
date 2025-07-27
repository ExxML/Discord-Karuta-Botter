import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import math
import json
import random

class TokenExtractor():
    def __init__(self):
        ### The number of accounts entered should be a multiple of 3 or else the script will not be able to auto-grab all dropped cards!
        # List your accounts (separated by commas) in the format: {"email": "example_email@gmail.com", "password": "example_password"}, ...
        # If you would rather use tokens, you can enter them as a list of strings in tokens.json.
        #   Example: ["token1", "token2", "token3"]
        # LEAVE THE LIST in tokens.json EMPTY if you would like to use account logins (below) instead.
        self.ACCOUNTS = [
        ]

        self.SAVE_TOKENS = True  # (bool) Choose whether to save tokens to file (tokens.json)

        try:
            with open("tokens.json", "r") as tokens_file:
                self.TOKENS = json.load(tokens_file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.TOKENS = []
        if not isinstance(self.TOKENS, list) or not all(isinstance(token, str) for token in self.TOKENS):
            input('⛔ Token Format Error ⛔\nExpected a list of strings. Example: ["token1", "token2", "token3"]')
            sys.exit()

        self.USER_AGENTS = [
            # Chrome - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.5790.102 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.5735.198 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/113.0.5672.63 Safari/537.36",

            # Chrome - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.5790.102 Safari/537.36",

            # Chrome - Linux
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0",

            # Firefox - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:116.0) Gecko/20100101 Firefox/116.0",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",

            # Firefox - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.5; rv:116.0) Gecko/20100101 Firefox/116.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12.6; rv:115.0) Gecko/20100101 Firefox/115.0",

            # Edge - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36 Edg/116.0.1938.81",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.5790.102 Safari/537.36 Edg/115.0.1901.188",

            # Safari - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.5 Safari/605.1.15",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6_3) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.4 Safari/605.1.15",

            # Safari - iOS (iPhone)
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/16.0 Mobile/15E148 Safari/604.1",

            # Chrome - Android
            "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.5790.102 Mobile Safari/537.36",

            # Firefox - Android
            "Mozilla/5.0 (Android 13; Mobile; rv:116.0) Gecko/116.0 Firefox/116.0",
            "Mozilla/5.0 (Android 12; Mobile; rv:115.0) Gecko/115.0 Firefox/115.0",

            # Opera - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36 OPR/102.0.4843.50",

            # Opera - Android
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Mobile Safari/537.36 OPR/70.0.3728.144",

            # Brave Browser - Windows
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36 Brave/116.0.5845.97",

            # Brave Browser - macOS
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/116.0.5845.97 Safari/537.36 Brave/116.0.5845.97"
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

    def extract_discord_token(self, email: str, password: str):
        try:
            # Navigate to Discord login
            self.driver.get("https://discord.com/login")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
            print("Login page loaded")
            # Find login fields and submit
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            email_field.send_keys(email)
            password_field.send_keys(password)
            print("Filled in credentials")
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            print("Clicked log in")
            WebDriverWait(self.driver, 15).until(lambda d: "/login" not in d.current_url)
            print("Discord loaded")
            
            # Update page to extract token from app
            self.driver.get("https://discord.com/app")

            # Execute JS to grab token from local storage
            token = self.driver.execute_script("return window.localStorage.getItem('token');")
            if token:
                print("Token extracted")
                return token[1:-1]  # Trim quotes
            else:
                print(f"No token found for {email}")
                return None
        except Exception as e:
            print(f"Error with {email}: {str(e)}")
            return None

    def main(self, num_channels: int):
        if self.TOKENS:
            print("ℹ️ Using tokens (from tokens.json) instead of account logins...")
            num_accounts = len(self.TOKENS)
        else:
            print("ℹ️ Using account logins instead of tokens...")
            num_accounts = len(self.ACCOUNTS)

        if num_accounts == 0:
            input("\n⛔ Account Error ⛔\nNo accounts found. Please enter at least 1 account in token_extractor.py or tokens.json.")
            sys.exit()
        
        if self.TOKENS:
            num_channels_need = math.ceil(len(self.TOKENS) / 3)  # Maximum 3 accounts per channel
        else:
            num_channels_need = math.ceil(len(self.ACCOUNTS) / 3)  # Maximum 3 accounts per channel
        if  num_channels_need != num_channels:
            input(f"\n⛔ Configuration Error ⛔\nYou have entered {num_channels} drop channel(s). You should have {num_channels_need} channel(s).")
            sys.exit()

        if num_accounts % 3 != 0:
            input(f"\n⚠️ Configuration Warning ⚠️\nThe number of accounts you entered is not a multiple of 3." +
                    f"\nThe script will only be able to auto-grab {(num_accounts * 3) - 2}/{num_accounts * 3} dropped cards. Press `Enter` if you wish to continue.")

        if self.TOKENS:
            return self.TOKENS

        # Executes if using account logins
        tokens = []
        for index, account in enumerate(self.ACCOUNTS):
            print("\nLoading new undetected Chrome...")
            self.load_chrome()
            print(f"Processing {index + 1}/{len(self.ACCOUNTS)}: {account['email']}...")
            token = self.extract_discord_token(account["email"], account["password"])
            print("Closing Chrome...")
            self.driver.quit()
            if token:
                tokens.append(token)

        num_tokens = len(tokens)
        if num_tokens == 0:
            input("\n⛔ Token Error ⛔\nNo tokens found. Please check your account info.")
            sys.exit()
        elif num_tokens != len(self.ACCOUNTS):
            input(f"\n⚠️ Configuration Warning ⚠️\nYou entered {len(self.ACCOUNTS)} accounts, but only {num_tokens} tokens were found.\nPress `Enter` if you wish to continue.")
        
        if self.SAVE_TOKENS:
            with open("tokens.json", "w") as tokens_file:
                json.dump(tokens, tokens_file)
                print("\nℹ️ Tokens saved to tokens.json")

        return tokens