"""Common utilities for github plugins"""

from github import Github
from github.GithubObject import GithubObject, NotSet

DEFAULT_API_URL = "https://api.github.com"


def ghconnect(token, organization=None, base_url=None):
    if base_url is None:
        base_url = DEFAULT_API_URL

    client = Github(base_url=base_url, login_or_token=token)

    return client.get_organization(organization) if organization else client.get_user()


class GithubObjectConfig:
    def __eq__(self, other):
        if isinstance(other, GithubObjectConfig):
            return super.__eq__(other)

        if isinstance(other, GithubObject):
            return self.__eq__(other.raw_data)

        if isinstance(other, dict):
            for key, val in other.items():
                if self[key] != val:
                    return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        for name, value in self.__dict__.items():
            if value is None:
                value = NotSet

            elif value == ...:
                value = NotSet

            yield name, value

    def asdict(self):
        return {k: v for k, v in self}
