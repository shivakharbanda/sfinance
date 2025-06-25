from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseFetcher:
    def __init__(self, base_url: str, chrome_binary_path):
        self.base_url = base_url.rstrip("/")

        self._logged_in = False
        self.chrome_binary_path = chrome_binary_path

        self.driver = self._init_driver()


    def _init_driver(self):
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-extensions")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)

        if self.chrome_binary_path:
            opts.binary_location = self.chrome_binary_path
            
        return webdriver.Chrome(options=opts)

    def get_driver(self):
        return self.driver

    def build_url(self, relative_url: str) -> str:
        return f"{self.base_url}/{relative_url.lstrip('/')}"

    def login(self, username: str, password: str):
        login_url = f"{self.base_url}/login/"
        self.driver.get(login_url)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "id_username"))
            )

            self.driver.find_element(By.ID, "id_username").send_keys(username)
            self.driver.find_element(By.ID, "id_password").send_keys(password)
            self.driver.find_element(By.CSS_SELECTOR, "form button[type='submit']").click()

            # Wait until we land on dashboard or see logout
            WebDriverWait(self.driver, 10).until(
                EC.url_contains("/dash/")
            )

            self._logged_in = True
            print("Login successful.")
        except Exception as e:
            raise RuntimeError(f"Login failed: {e}")

        
    def is_logged_in(self):
        return self._logged_in

    def close(self):
        self.driver.quit()
