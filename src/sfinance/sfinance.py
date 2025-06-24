from .fetcher import BaseFetcher
from .ticker import Ticker

class SFinance:
    def __init__(self, base_url, chrome_binary_path=None):
        self.fetcher = BaseFetcher(base_url, chrome_binary_path)

    def ticker(self, symbol: str):
        return Ticker(symbol, self.fetcher)

    def close(self):
        self.fetcher.close()