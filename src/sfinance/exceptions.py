class TickerNotFound(Exception):
    """Raised when the requested ticker is not found on the site."""
    pass

class LoginRequiredError(Exception):
    """Raised when login is required but credentials were not provided."""
    pass