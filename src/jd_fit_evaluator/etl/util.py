import os

GH_API = "https://harvest.greenhouse.io/v1"

def gh_auth():
    from ..config import settings
    token = settings.gh_token or ""
    return (token, "")
