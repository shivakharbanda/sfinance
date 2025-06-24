========
sfinance
========

.. image:: https://img.shields.io/pypi/v/sfinance.svg
        :target: https://pypi.python.org/pypi/sfinance

.. image:: https://readthedocs.org/projects/sfinance/badge/?version=latest
        :target: https://sfinance.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

sfinance is a lightweight Python library for automating the extraction of financial tables from publicly accessible, structured HTML pages.

It uses Selenium and BeautifulSoup under the hood to simulate browser behavior and extract data into pandas DataFrames for further analysis.

This tool is intended for personal and educational use only.

* Free software: Apache Software License 2.0
* Documentation: https://sfinance.readthedocs.io


Usage
-----

Install the package (once published on PyPI):

.. code-block:: shell

    pip install sfinance

Use it like this:

.. code-block:: python

    from sfinance.sfinance import StockDataFetcher

    url = "https://www.screener.in/company/INFY/consolidated/"  # Full URL is required
    fetcher = StockDataFetcher(url)

    overview = fetcher.get_company_overview()
    income = fetcher.get_income_statement()
    balance = fetcher.get_balance_sheet()
    cashflow = fetcher.get_cash_flow()
    shareholding = fetcher.get_shareholding()

    print(overview, income, balance, cashflow, shareholding)

    fetcher.close()

This will return clean, structured pandas DataFrames from dynamically rendered pages. You are expected to supply valid URLs yourself. The package does not suggest or pre-configure any third-party endpoints.

---

Legal Disclaimer
----------------

This project is an independent, educational, and non-commercial utility.

- It is **not affiliated with, endorsed by, or sponsored by Screener.in, Mittal Analytics Private Limited, or any other third-party data provider**.
- `sfinance` **does not provide, store, host, or distribute** any financial data.
- It only reads **publicly accessible** web content **on-demand** using browser automation. No data is cached, saved, or redistributed.
- All access is controlled by the user via input URLs. You are fully responsible for your use of this tool.
- This library is intended for **personal, educational, and non-commercial** purposes only.

Please respect the terms of service of any website you access. Use responsibly.



Features
--------

* Uses Selenium to render dynamic content
* Parses financial tables with BeautifulSoup
* Extracts income statement, balance sheet, cash flow, shareholding, and company overview
* Outputs pandas DataFrames for analysis

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

Legal Disclaimer
----------------

This project is not affiliated with, endorsed by, or sponsored by Screener.in, Mittal Analytics Private Limited, or any other third-party data provider.

This tool does not store, modify, or distribute data. It simply reads publicly viewable HTML pages when accessed by the user, using standard browser automation techniques.

Users are solely responsible for ensuring that their use of this software complies with the terms of service of any website they access.
