=======
History
=======

0.2.0 (2026-03-30)
------------------

* Added document section support: ``get_announcements()``, ``get_annual_reports()``,
  ``get_credit_ratings()``, and ``get_concalls()`` — all return pandas DataFrames.
* Added ``download(url, folder_path, filename=None)`` for one-off URL downloads.
* Added ``download_documents(doc_type, folder_path, ...)`` for bulk downloads with
  filtering by ``year``, ``period``, ``tab``, ``n``, and ``link_type``.
* All document and download methods require login (raises ``LoginRequiredError``).
* Fixed URL encoding for paths containing spaces (e.g. Crisil report URLs).
* Fixed domain-specific Referer header to reduce 403 errors on external PDF servers.

0.1.0 (2025-06-24)
------------------

* First release on PyPI.

