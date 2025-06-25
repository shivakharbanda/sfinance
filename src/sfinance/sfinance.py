from .fetcher import BaseFetcher
from .ticker import Ticker
from .stock_screener import StockScreener

class SFinance:
    def __init__(self, base_url, chrome_binary_path=None):
        self.fetcher = BaseFetcher(base_url, chrome_binary_path)

    def login(self, username: str, password: str):
        self.fetcher.login(username, password)

    def ticker(self, symbol: str):
        return Ticker(symbol, self.fetcher)
    
    def screener(self):
        return StockScreener(self.fetcher)

    def close(self):
        self.fetcher.close()