from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class BaseFetcher:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
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
        return webdriver.Chrome(options=opts)

    def get_driver(self):
        return self.driver

    def build_url(self, relative_url: str) -> str:
        return f"{self.base_url}/{relative_url.lstrip('/')}"

    def close(self):
        self.driver.quit()
