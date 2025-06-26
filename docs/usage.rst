=====
Usage
=====
---

Basic Usage
===========

Create an instance of `SFinance` and extract data for a given stock:

.. code-block:: python

    from sfinance.sfinance import SFinance

    # Start SFinance instance (you may optionally specify the Chrome binary)
    # Example: using "https://www.screener.in/" as the source site
    sf = SFinance("https://example.com/")

    # Get a ticker object for a given symbol
    ticker = sf.ticker("INFY")

    # Fetch company-level data
    print(ticker.get_overview())             # Returns dict with 'Name' and 'About'
    print(ticker.get_income_statement())     # Returns a DataFrame
    print(ticker.get_balance_sheet())        # Returns a DataFrame
    print(ticker.get_cash_flow())            # Returns a DataFrame
    print(ticker.get_quarterly_results())    # Returns a DataFrame
    print(ticker.get_shareholding())         # Returns a DataFrame
    print(ticker.get_peer_comparison())      # Returns a DataFrame

    # Close the browser when done
    sf.close()

---

Login (for Screener features)
=============================

Some functionality like stock screening **requires login**. You must pass your credentials directly (no environment variables used by default):

.. code-block:: python

    # Example: using Screener.in as the source site
    sf = SFinance("https://example.com/")
    sf.login("your_email@example.com", "your_password")

    # Check login status
    print(sf.fetcher.is_logged_in())

    sf.close()

If login fails (wrong credentials or CAPTCHA), an exception is raised.

---

Stock Screening
===============

After logging in, you can use the built-in stock screener to run custom financial queries.

.. code-block:: python

    sf = SFinance("https://example.com/")
    sf.login("your_email@example.com", "your_password")

    screener = sf.screener()

    df = screener.load_raw_query(
        query="Return on equity > 15 AND Piotroski score > 7",
        sort="Market Capitalization",
        order="desc",
        page=1
    )

    print(df)

    sf.close()
---

Headless Chrome Notes
=====================

`sfinance` uses Selenium with a headless Chrome driver under the hood. By default, it launches Chrome from your system path.

To specify a custom Chrome binary:

.. code-block:: python

    sf = SFinance("https://example.com/", chrome_binary_path="/path/to/chrome")

---

Error Handling
==============

- `TickerNotFound` – Raised if a stock symbol is not found.
- `LoginRequiredError` – Raised if screener is accessed without login.

.. code-block:: python

    from sfinance.exceptions import TickerNotFound, LoginRequiredError

    try:
        ticker = sf.ticker("INVALID123")
    except TickerNotFound:
        print("Invalid ticker symbol")

    try:
        screener = sf.screener()
        df = screener.load_raw_query(query="ROE > 20")
    except LoginRequiredError:
        print("Please login first")

---

Closing the Session
===================

Always call `.close()` when you're done:

.. code-block:: python

    sf.close()
