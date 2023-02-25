"""Utility class for all managers."""

API_VERSION = "2022-11-28"
API_BASE = "http://api.github.com"


class InternalAPI:
    def __init__(self, base_url, headers=None):
        self.headers = headers
        self.base_url = base_url

    def get(self, url, params=None):
        ...

    def patch(self, url, params=None):
        ...

    def post(self, url, params=None):
        ...

    def delete(self, url, params=None):
        ...


class ResourceManager:
    def __init__(self, token, base_url=API_BASE):
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
        }

        self.api = InternalAPI(base_url=base_url, headers=headers)
