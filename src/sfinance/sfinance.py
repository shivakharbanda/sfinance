import io
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class StockDataFetcher:
    def __init__(self, url: str):
        self.url = url
        self.driver = self._init_driver()
        self.page = self._load_page()
        self.soup = BeautifulSoup(self.driver.page_source, "html.parser")

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

    def _load_page(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(5)

        # Expand any dynamic sections (buttons triggering content reveal)
        button_selectors = [
            "button[onclick^='Company.showSchedule']",
            "button[data-tab-id='quarterly-shp']",
            "button[onclick^='Company.showShareholders']",
            "div.about button.show-more-button"
        ]

        for selector in button_selectors:
            try:
                for btn in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.2)
            except:
                continue

        time.sleep(1)

    def _extract_table(self, section_id: str):
        try:
            table = self.soup.select_one(f"section#{section_id} table.data-table")
            if not table:
                raise ValueError(f"No table found in section '{section_id}'")
            df = pd.read_html(io.StringIO(str(table)), flavor="bs4")[0]
            df.rename(columns={df.columns[0]: "Metric"}, inplace=True)
            return self._clean_df(df)
        except Exception as e:
            print(f"Error extracting section {section_id}: {e}")
            return pd.DataFrame()

    def _clean_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df

        month_map = {
            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06',
            'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
        }

        new_columns = ['Metric']
        for col in df.columns[1:]:
            try:
                month, year = col.strip().split()
                new_columns.append(f"{year}-{month_map[month]}")
            except (ValueError, KeyError):
                new_columns.append(col)
        df.columns = new_columns

        df["Metric"] = (
            df["Metric"]
            .astype(str)
            .str.replace(r"\s*[-+]\s*$", "", regex=True)
            .str.strip()
        )

        for col in df.columns[1:]:
            s = df[col].astype(str).str.strip()
            if s.str.endswith("%").any():
                df[col] = (
                    s.str.rstrip("%")
                     .str.replace(",", "", regex=False)
                     .astype(float)
                     .div(100)
                )
            else:
                df[col] = (
                    s.str.replace(",", "", regex=False)
                     .replace("nan", None)
                     .astype(float, errors='ignore')
                )

        df.dropna(how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df

    def get_income_statement(self):
        return self._extract_table("profit-loss")

    def get_balance_sheet(self):
        return self._extract_table("balance-sheet")

    def get_cash_flow(self):
        return self._extract_table("cash-flow")

    def get_quarterly_results(self):
        return self._extract_table("quarters")

    def get_shareholding(self):
        return self._extract_table("shareholding")

    def get_company_overview(self):
        try:
            name = self.soup.find("h1")
            about = self.soup.select_one("div.about p")
            overview = {
                "Name": name.text.strip() if name else None,
                "About": about.text.strip() if about else None
            }
            return overview
        except Exception as e:
            print(f"Error extracting overview: {e}")
            return {}

    def close(self):
        self.driver.quit()
