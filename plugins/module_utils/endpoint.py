"""Working with standard Github endpoints."""

import requests

API_URL = "https://api.github.com"
API_VERSION = "2022-11-28"


class GithubEndpoint:
    def __init__(self, endpoint, token):
        self.endpoint = endpoint

        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": API_VERSION,
        }

    def get(self):
        ...

    def patch(self):
        ...

    def post(self):
        ...

    def delete(self, params=None):
        return requests.delete(self.endpoint, headers=self.headers, params=params)


class LabelEndpoint(GithubEndpoint):
    def __init__(self, owner, repo, name):
        super().__init__(f"/repos/{owner}/{repo}/labels/{name}")
