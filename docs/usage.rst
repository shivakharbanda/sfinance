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

Documents
=========

Access a company's document section (announcements, annual reports, credit ratings, concalls).
**Login is required** for all document methods.

.. code-block:: python

    sf = SFinance("https://example.com/")
    sf.login("your_email@example.com", "your_password")

    ticker = sf.ticker("INFY")

    # Announcements — tab="recent" (default) or "important"
    df = ticker.get_announcements()
    df = ticker.get_announcements(tab="important")
    # Columns: title, subtitle, url

    # Annual reports
    df = ticker.get_annual_reports()
    # Columns: title, source, url

    # Credit ratings
    df = ticker.get_credit_ratings()
    # Columns: title, subtitle, url

    # Concalls — columns: period, transcript_url, ppt_url, rec_url (None if unavailable)
    df = ticker.get_concalls()

---

Downloading Documents
=====================

**Login is required** for all download methods.

Download any single URL directly:

.. code-block:: python

    # Filename auto-derived from URL if not provided
    ticker.download(url, "/path/to/folder")
    ticker.download(url, "/path/to/folder", filename="custom_name.pdf")

    # Example: download the latest annual report
    reports = ticker.get_annual_reports()
    ticker.download(reports.iloc[0]["url"], "/path/to/folder")

Bulk download all documents of a type:

.. code-block:: python

    # All recent announcements
    ticker.download_documents("announcements", "/path/to/folder")

    # Important announcements, latest 3
    ticker.download_documents("announcements", "/path/to/folder", tab="important", n=3)

    # All annual reports
    ticker.download_documents("annual_reports", "/path/to/folder")

    # Specific year(s)
    ticker.download_documents("annual_reports", "/path/to/folder", year=2025)
    ticker.download_documents("annual_reports", "/path/to/folder", year=[2024, 2025])

    # All credit ratings
    ticker.download_documents("credit_ratings", "/path/to/folder")

    # Concall transcripts — all, or filtered by period / latest N
    ticker.download_documents("concalls", "/path/to/folder", link_type="transcript")
    ticker.download_documents("concalls", "/path/to/folder", period="Jan 2026", link_type="transcript")
    ticker.download_documents("concalls", "/path/to/folder", n=5, link_type="all")

``download_documents`` returns a list of saved file paths. Failed downloads are printed
and skipped without raising an exception.

**Supported ``link_type`` values for concalls:** ``"transcript"``, ``"ppt"``, ``"rec"``, ``"all"``
(YouTube REC links are automatically skipped during download.)

---

Error Handling
==============

- `TickerNotFound` – Raised if a stock symbol is not found.
- `LoginRequiredError` – Raised if document/screener methods are accessed without login.

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
