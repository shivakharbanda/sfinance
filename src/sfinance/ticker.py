import io
import os
import re
import time
import urllib.request
from urllib.parse import quote, urlparse, urlunparse
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from sfinance.exceptions import TickerNotFound, LoginRequiredError


class Ticker:
    _DOWNLOAD_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/pdf,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

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

        # Open a dedicated tab — shares the login session (same browser),
        # but isolates page state so tickers don't overwrite each other's soup.
        self.driver.execute_script("window.open('about:blank', '_blank');")
        self.window_handle = self.driver.window_handles[-1]
        self.driver.switch_to.window(self.window_handle)

        self.soup = self._load_and_parse()
        self._documents_loaded = False

    def _activate(self):
        """Switch the shared driver focus to this ticker's tab."""
        if self.driver.current_window_handle != self.window_handle:
            self.driver.switch_to.window(self.window_handle)

    def _load_and_parse(self):
        self._activate()
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

    def _ensure_documents_loaded(self):
        if self._documents_loaded:
            return
        self._activate()
        try:
            for btn in self.driver.find_elements(By.CSS_SELECTOR, "#documents button.show-more-button"):
                if btn.is_displayed():
                    btn.click()
                    time.sleep(0.3)
            time.sleep(1)
            self.soup = BeautifulSoup(self.driver.page_source, "html.parser")
            self._documents_loaded = True
        except Exception as e:
            print(f"Error loading documents section: {e}")

    def get_peer_comparison(self):
        self._activate()
        try:
            # warehouse_id is already in the loaded soup — no JS wait needed
            info = self.soup.find("div", id="company-info")
            if not info:
                print(f"No company-info div found for {self.symbol}")
                return pd.DataFrame()

            warehouse_id = info.get("data-warehouse-id")
            if not warehouse_id:
                print(f"No warehouse_id found for {self.symbol}")
                return pd.DataFrame()

            # Hit the API directly using Selenium's authenticated session cookies
            api_url = f"https://www.screener.in/api/company/{warehouse_id}/peers/"
            cookies = {c["name"]: c["value"] for c in self.driver.get_cookies()}
            headers = {
                "Referer": self.url,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "text/html, */*",
            }

            resp = requests.get(api_url, cookies=cookies, headers=headers, timeout=15)
            resp.raise_for_status()

            # pd.read_html handles column names, dtypes, and numeric parsing automatically.
            # Median row (S.No. = NaN) is kept — it's useful context.
            tables = pd.read_html(io.StringIO(resp.text))
            if not tables:
                return pd.DataFrame()
            return tables[0].reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching peer comparison for {self.symbol}: {e}")
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

    def get_announcements(self, tab: str = "recent") -> pd.DataFrame:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to access announcements.")
        if tab not in {"recent", "important"}:
            raise ValueError("tab must be 'recent' or 'important'")
        self._activate()
        try:
            self._ensure_documents_loaded()
            if tab == "recent":
                soup = self.soup
            else:
                btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button[onclick*='announcements/important']"
                )
                btn.click()
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#company-announcements-tab ul li")
                    )
                )
                time.sleep(0.5)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")

            container = soup.select_one("#company-announcements-tab ul.list-links")
            if not container:
                return pd.DataFrame()

            rows = []
            for li in container.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue
                href = a.get("href", "").strip() or None
                subtitle_div = a.find("div")
                subtitle = subtitle_div.get_text(strip=True) if subtitle_div else None
                title = a.get_text(separator=" ", strip=True)
                if subtitle:
                    title = title.replace(subtitle, "").strip()
                rows.append({"title": title, "subtitle": subtitle, "url": href})

            return pd.DataFrame(rows, columns=["title", "subtitle", "url"])
        except Exception as e:
            print(f"Error extracting announcements: {e}")
            return pd.DataFrame()

    def get_annual_reports(self) -> pd.DataFrame:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to access annual reports.")
        try:
            self._ensure_documents_loaded()
            container = self.soup.select_one("div.annual-reports ul.list-links")
            if not container:
                return pd.DataFrame()

            rows = []
            for li in container.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue
                href = a.get("href", "").strip() or None
                subtitle_div = a.find("div")
                source = subtitle_div.get_text(strip=True) if subtitle_div else None
                title = a.get_text(separator=" ", strip=True)
                if source:
                    title = title.replace(source, "").strip()
                rows.append({"title": title, "source": source, "url": href})

            return pd.DataFrame(rows, columns=["title", "source", "url"])
        except Exception as e:
            print(f"Error extracting annual reports: {e}")
            return pd.DataFrame()

    def get_credit_ratings(self) -> pd.DataFrame:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to access credit ratings.")
        try:
            self._ensure_documents_loaded()
            container = self.soup.select_one("div.credit-ratings ul.list-links")
            if not container:
                return pd.DataFrame()

            rows = []
            for li in container.find_all("li", recursive=False):
                a = li.find("a")
                if not a:
                    continue
                href = a.get("href", "").strip() or None
                subtitle_div = a.find("div")
                subtitle = subtitle_div.get_text(strip=True) if subtitle_div else None
                title = a.get_text(separator=" ", strip=True)
                if subtitle:
                    title = title.replace(subtitle, "").strip()
                rows.append({"title": title, "subtitle": subtitle, "url": href})

            return pd.DataFrame(rows, columns=["title", "subtitle", "url"])
        except Exception as e:
            print(f"Error extracting credit ratings: {e}")
            return pd.DataFrame()

    def get_concalls(self) -> pd.DataFrame:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to access concalls.")
        try:
            self._ensure_documents_loaded()
            container = self.soup.select_one("div.concalls ul.list-links")
            if not container:
                return pd.DataFrame()

            rows = []
            for li in container.find_all("li", recursive=False):
                period_div = li.select_one("div.font-weight-500.font-size-15")
                period = period_div.get_text(strip=True) if period_div else None

                links = {}
                for a in li.find_all("a", class_="concall-link"):
                    text = a.get_text(strip=True).lower()
                    href = a.get("href", "").strip() or None
                    if text in ("transcript", "ppt", "rec"):
                        links[text] = href

                rows.append({
                    "period": period,
                    "transcript_url": links.get("transcript"),
                    "ppt_url": links.get("ppt"),
                    "rec_url": links.get("rec"),
                })

            df = pd.DataFrame(rows, columns=["period", "transcript_url", "ppt_url", "rec_url"])
            for col in ["transcript_url", "ppt_url", "rec_url"]:
                df[col] = [v if isinstance(v, str) else None for v in df[col]]
            return df
        except Exception as e:
            print(f"Error extracting concalls: {e}")
            return pd.DataFrame()

    def _encode_url(self, url: str) -> str:
        p = urlparse(url)
        return urlunparse(p._replace(path=quote(p.path, safe="/")))

    def _make_headers(self, url: str) -> dict:
        p = urlparse(url)
        referer = f"{p.scheme}://{p.netloc}/"
        return {**self._DOWNLOAD_HEADERS, "Referer": referer}

    def download(self, url: str, folder_path: str, filename: str = None) -> str:
        if not self.fetcher.is_logged_in():
            raise LoginRequiredError("Login required to download documents.")
        if not url:
            raise ValueError("url cannot be empty")
        os.makedirs(folder_path, exist_ok=True)
        if not filename:
            filename = url.split("?")[0].rstrip("/").split("/")[-1] or "document"
        dest = os.path.join(folder_path, filename)
        encoded = self._encode_url(url)
        req = urllib.request.Request(encoded, headers=self._make_headers(url))
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(dest, "wb") as f:
                f.write(response.read())
        return dest

    def download_documents(self, doc_type: str, folder_path: str, link_type: str = "all",
                           tab: str = "recent", year=None, period=None, n: int = None) -> list:
        valid_doc_types = {"announcements", "annual_reports", "credit_ratings", "concalls"}
        valid_link_types = {"transcript", "ppt", "rec", "all"}
        if doc_type not in valid_doc_types:
            raise ValueError(f"doc_type must be one of {valid_doc_types}")
        if link_type not in valid_link_types:
            raise ValueError(f"link_type must be one of {valid_link_types}")

        os.makedirs(folder_path, exist_ok=True)

        def sanitize(text: str) -> str:
            return re.sub(r"[^\w\s-]", "", text).strip().replace(" ", "_")

        pairs = []

        if doc_type == "announcements":
            df = self.get_announcements(tab=tab)
            if n is not None:
                df = df.head(n)
            for i, row in df.iterrows():
                if not row["url"]:
                    continue
                name = sanitize(row["title"] or "")[:40]
                pairs.append((row["url"], f"announcement_{i + 1}_{name}.pdf"))

        elif doc_type == "annual_reports":
            df = self.get_annual_reports()
            if year is not None:
                years = [year] if isinstance(year, int) else list(year)
                df = df[df["title"].str.extract(r"(\d{4})")[0].astype(float).isin(years)]
            if n is not None:
                df = df.head(n)
            for i, row in df.iterrows():
                if not row["url"]:
                    continue
                year_match = re.search(r"\d{4}", row["title"] or "")
                yr = year_match.group() if year_match else str(i + 1)
                source = sanitize(row["source"] or "")
                filename = f"annual_report_{yr}_{source}.pdf" if source else f"annual_report_{yr}.pdf"
                pairs.append((row["url"], filename))

        elif doc_type == "credit_ratings":
            df = self.get_credit_ratings()
            if n is not None:
                df = df.head(n)
            for i, row in df.iterrows():
                if not row["url"]:
                    continue
                path_no_query = row["url"].split("?")[0].rstrip("/")
                ext = os.path.splitext(path_no_query)[1] or ".pdf"
                subtitle = row.get("subtitle") or ""
                date_match = re.search(r"\d{1,2}\s+\w+\s+\d{4}", subtitle)
                date_str = sanitize(date_match.group()) if date_match else str(i + 1)
                pairs.append((row["url"], f"credit_rating_{i + 1}_{date_str}{ext}"))

        elif doc_type == "concalls":
            df = self.get_concalls()
            if period is not None:
                periods = [period] if isinstance(period, str) else list(period)
                periods_lower = [p.lower() for p in periods]
                df = df[df["period"].str.lower().isin(periods_lower)]
            if n is not None:
                df = df.head(n)
            col_map = {"transcript": "transcript_url", "ppt": "ppt_url", "rec": "rec_url"}
            types_to_fetch = list(col_map.keys()) if link_type == "all" else [link_type]
            for _, row in df.iterrows():
                p = sanitize(row["period"] or "unknown")
                for lt in types_to_fetch:
                    url = row.get(col_map[lt])
                    if not isinstance(url, str) or not url:
                        continue
                    if "youtube.com" in url or "youtu.be" in url:
                        continue
                    pairs.append((url, f"concall_{p}_{lt}.pdf"))

        downloaded = []
        for url, filename in pairs:
            dest = os.path.join(folder_path, filename)
            try:
                req = urllib.request.Request(self._encode_url(url), headers=self._make_headers(url))
                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(dest, "wb") as f:
                        f.write(response.read())
                downloaded.append(dest)
            except Exception as e:
                print(f"Failed to download {url}: {e}")

        return downloaded

    def close(self):
        try:
            self._activate()
            self.driver.close()  # closes just this tab; BaseFetcher.close() quits the browser
        except Exception:
            pass
