import pandas as pd
import logging
import re
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from .exceptions import LoginRequiredError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class StockScreener:
    def __init__(self, fetcher):
        self.fetcher = fetcher
        self.driver = self.fetcher.get_driver()

    def _parse_table(self, html):
        soup = BeautifulSoup(html, "html.parser")
        table = soup.select_one("table.data-table")
        if not table:
            return pd.DataFrame()

        rows = table.find_all("tr")
        data = []
        headers = []

        for row in rows:
            cells = row.find_all(["th", "td"])
            texts = [c.get_text(strip=True) for c in cells]

            if row.find("th"):
                if not headers:
                    headers = texts
                continue

            if row.find("td") and len(texts) == len(headers):
                data.append(texts)

        return pd.DataFrame(data, columns=headers)

    def load_raw_query(self, query: str, sort: str = "", order: str = "", latest: bool = True, page: int = 1) -> pd.DataFrame:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to access this screen.")

        from urllib.parse import urlencode, quote_plus

        query_params = {
            "query": query,
            "sort": sort,
            "order": order,
            "latest": "on" if latest else "",
            "page": page
        }

        base_path = "screen/raw/"
        encoded = urlencode(query_params, quote_via=quote_plus)
        url = self.fetcher.build_url(f"{base_path}?{encoded}")

        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table.data-table"))
        )

        html = self.driver.page_source
        return self._parse_table(html)
