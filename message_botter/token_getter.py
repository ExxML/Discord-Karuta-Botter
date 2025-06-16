import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# List all accounts in the format: {"email": "example_email@gmail.com", "password": "example_password"}
ACCOUNTS = [
]

class TokenGetter():
    def __init__(self):
        pass

    def setup(self):
        options = uc.ChromeOptions()
        options.add_argument('--headless=new')  # Comment for non-headless mode if needed
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-infobars')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = uc.Chrome(options = options, use_subprocess = True)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # Browser spoofer

    def get_discord_token(self, email, password):
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
            time.sleep(1)  # Delay to mimic human behavior
            self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
            print("Clicked log in")
            WebDriverWait(self.driver, 10).until(lambda d: "/login" not in d.current_url)
            print("Discord loaded")
            
            # Update page to get token from app
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

    def main(self):
        tokens = []
        for account in ACCOUNTS:
            print("Loading new undetected Chrome...")
            self.setup()
            print(f"Processing {account['email']}...")
            token = self.get_discord_token(account["email"], account["password"])
            print("Closing Chrome...\n")
            self.driver.quit()
            if token:
                tokens.append(token)
        return tokens