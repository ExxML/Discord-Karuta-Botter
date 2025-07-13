import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sys
import math
import json

class TokenExtractor():
    def __init__(self):
        ### Enter at least 3 accounts so the script can auto-grab all cards!
        ### The number of accounts entered should also be a multiple of 3 or else the script will not be able to function at full capacity!

        # List your accounts (separated by commas) in the format: {"email": "example_email@gmail.com", "password": "example_password"}, ...
        # If you would rather use tokens, you can enter them as a list of strings in tokens.json.
        #   Example: ["token1", "token2", "token3"]
        # LEAVE THE LIST in tokens.json EMPTY if you would like to use account logins (below) instead.
        self.ACCOUNTS = [
        ]

        self.SAVE_TOKENS = True  # Choose whether to save tokens to file (tokens.json)

        with open("tokens.json", "r") as tokens_file:
            try:
                self.TOKENS = json.load(tokens_file)
            except json.JSONDecodeError:
                self.TOKENS = []
        if not isinstance(self.TOKENS, list) or not all(isinstance(token, str) for token in self.TOKENS):
            input('⛔ Token Format Error ⛔\nExpected a list of strings. Example: ["token1", "token2", "token3"]')
            sys.exit()

    def load_chrome(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless = new')  # Comment for non-headless mode if needed
        options.add_argument('--disable-blink-features = AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options = options, use_subprocess = True)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Browser spoofer

    def extract_discord_token(self, email: str, password: str):
        try:
            # Navigate to Discord login
            self.driver.get("https://discord.com/login")
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[@type = 'submit']")))
            print("Login page loaded")
            # Find login fields and submit
            email_field = self.driver.find_element(By.NAME, "email")
            password_field = self.driver.find_element(By.NAME, "password")
            email_field.send_keys(email)
            password_field.send_keys(password)
            print("Filled in credentials")
            self.driver.find_element(By.XPATH, "//button[@type = 'submit']").click()
            print("Clicked log in")
            WebDriverWait(self.driver, 10).until(lambda d: "/login" not in d.current_url)
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
            print("ℹ️ Using account logins instead of tokens...\n")
            num_accounts = len(self.ACCOUNTS)

        num_account_warning = num_accounts < 3
        if num_accounts == 0:
            input("⛔ Account Error ⛔\nNo accounts found. Please enter at least 1 account in token_extractor.py or tokens.json.")
            sys.exit()
        elif num_account_warning:
            input(f"⚠️ Configuration Warning ⚠️\nYou have entered less than 3 accounts. The script will only be able to auto-grab {num_accounts}/3 cards dropped.\nPress `Enter` if you wish to continue.")
        
        multiple_account_warning = num_accounts > 3 and num_accounts % 3 != 0
        if multiple_account_warning:
            if self.TOKENS:
                for _ in range(num_accounts % 3):
                    del self.TOKENS[-1]  # Trim number of accounts to a multiple of 3
            else:
                for _ in range(num_accounts % 3):
                    del self.ACCOUNTS[-1]  # Trim number of accounts to a multiple of 3
            if self.TOKENS:
                input(f"⚠️ Configuration Warning ⚠️\nThe number of accounts you entered is not a multiple of 3. \nThe script will only be functioning at {int((len(self.TOKENS) / num_accounts) * 100)}% capacity.\nPress `Enter` if you wish to continue.")
            else:
                input(f"⚠️ Configuration Warning ⚠️\nThe number of accounts you entered is not a multiple of 3. \nThe script will only be functioning at {int((len(self.ACCOUNTS) / num_accounts) * 100)}% capacity.\nPress `Enter` if you wish to continue.")
        
        if self.TOKENS:
            num_channels_need = math.ceil(len(self.TOKENS) / 3)  # Maximum 3 accounts per channel
        else:
            num_channels_need = math.ceil(len(self.ACCOUNTS) / 3)  # Maximum 3 accounts per channel
        if  num_channels_need != num_channels:
            input(f"⛔ Configuration Error ⛔\nYou have entered {num_channels} drop channel(s). You should have {num_channels_need} channel(s).")
            sys.exit()

        if self.TOKENS:
            return self.TOKENS

        # Executes if using account logins
        tokens = []
        for account in self.ACCOUNTS:
            if account == self.ACCOUNTS[0] and not num_account_warning and not multiple_account_warning:
                print("Loading new undetected Chrome...")
            else:
                print("\nLoading new undetected Chrome...")  # \n ONLY if not first account or account_warning
            self.load_chrome()
            print(f"Processing {account['email']}...")
            token = self.extract_discord_token(account["email"], account["password"])
            print("Closing Chrome...")
            self.driver.quit()
            if token:
                tokens.append(token)

        num_tokens = len(tokens)
        if num_tokens == 0:
            input("⛔ Token Error ⛔\nNo tokens found. Please check your account info.")
            sys.exit()
        elif num_tokens != len(self.ACCOUNTS):
            input(f"⚠️ Configuration Warning ⚠️\nYou entered {len(self.ACCOUNTS)} accounts, but only {num_tokens} tokens were found.\nPress `Enter` if you wish to continue.")
        
        if self.SAVE_TOKENS:
            with open("tokens.json", "w") as tokens_file:
                json.dump(tokens, tokens_file)
                print("ℹ️ Tokens saved to tokens.json")

        return tokens