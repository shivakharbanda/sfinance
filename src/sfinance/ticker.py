import io
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from sfinance.exceptions import TickerNotFound


class Ticker:
    def __init__(self, symbol: str, fetcher, mode: str = "consolidated"):
        self.symbol = symbol.upper()
        self.fetcher = fetcher
        self.driver = self.fetcher.get_driver()
        
        if mode not in {"consolidated", "standalone"}:
            raise ValueError("mode must be 'consolidated' or 'standalone'")
        self.mode = mode

        suffix = "/consolidated/" if self.mode == "consolidated" else "/"
        self.relative_path = f"company/{self.symbol}{suffix}"

        self.url = self.fetcher.build_url(self.relative_path)
        self.soup = self._load_and_parse()


    def _load_and_parse(self):
        self.driver.get(self.url)
        self.driver.implicitly_wait(5)

        # Check for 404 condition
        if "Error 404" in self.driver.page_source or "No CompanyCode matches the given query" in self.driver.page_source:
            raise TickerNotFound(f"Ticker '{self.symbol}' not found at {self.url}")

        for selector in [
            "button[onclick^='Company.showSchedule']",
            "button[data-tab-id='quarterly-shp']",
            "button[onclick^='Company.showShareholders']",
            "div.about button.show-more-button"
        ]:
            try:
                for btn in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if btn.is_displayed():
                        btn.click()
                        time.sleep(0.2)
            except:
                continue

        time.sleep(1)
        return BeautifulSoup(self.driver.page_source, "html.parser")
    
    def get_peer_comparison(self):
        try:
            table = self.soup.select_one("#peers-table-placeholder table.data-table")
            if not table:
                raise ValueError("Peer comparison table not found.")

            df = pd.read_html(io.StringIO(str(table)), flavor="bs4")[0]

            # Ensure headers are correct
            expected_cols = [
                "S.No.", "Name", "CMP", "P/E", "Mar Cap", "Div Yld",
                "NP Qtr", "Qtr Profit Var", "Sales Qtr", "Qtr Sales Var", "ROCE"
            ]
            df.columns = expected_cols[:len(df.columns)]  # truncate in case footer row is smaller

            # Drop the Median row from <tfoot> if it exists
            df = df[~df["S.No."].astype(str).str.contains("Median", na=False)]

            # Clean up numeric fields
            for col in df.columns[2:]:
                df[col] = (
                    df[col].astype(str)
                        .str.replace(",", "", regex=False)
                        .replace("-", None)
                        .astype(float)
                )

            # Strip any whitespace in "Name"
            df["Name"] = df["Name"].astype(str).str.strip()

            return df.reset_index(drop=True)

        except Exception as e:
            print(f"Error extracting peer comparison: {e}")
            return pd.DataFrame()


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

    def get_overview(self):
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
