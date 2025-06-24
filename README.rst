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
