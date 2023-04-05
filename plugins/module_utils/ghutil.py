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
    """Representation of a desired Github configuration for a specific resource."""

    def __eq__(self, other):
        """Determine if the current config matches the other config.

        In this context, equality is used to determine if a resource should be changed.  It does not
        imply that the objects themselves are equal in all other aspects.
        """

        if isinstance(other, GithubObjectConfig):
            return self.__eq__(other.asdict())

        if isinstance(other, GithubObject):
            return self.__eq__(other.raw_data)

        if isinstance(other, dict):
            for key, val in self:
                if val == NotSet:
                    continue

                if key not in other:
                    continue

                if other[key] != val:
                    return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __iter__(self):
        """Return all fields in this config, suitable for use in the Github API."""
        for name, value in self.__dict__.items():
            if value is None:
                value = NotSet

            elif value == ...:
                value = NotSet

            yield name, value

    def asdict(self):
        """Return the current config as a dictionary, suitable for use in the Github API."""
        return dict(self)
