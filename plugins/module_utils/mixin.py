"""Common utilities for github plugins"""

from github.GithubObject import GithubObject


class GithubObjectMixin:
    """Common methods for github object wrappers."""

    def __contains__(self, name):
        return self.get(name) is not None

    def __getitem__(self, name):
        item = self.get(name)

        if item is None:
            raise KeyError(f"Resource does not exist - {name}")

        return item

    def edit(self, obj: GithubObject, config: dict, check_mode=False):
        result = {"changed": False, "data": obj.raw_data}

        changed = False

        # find out if anything needs to change
        for key, val in config.items():
            state = obj.raw_data.get(key, None)

            if state == val:
                continue

            # any changes require an edit
            changed = True
            break

        # look for the easy way out
        if not changed:
            return result

        # apply current config
        if not check_mode:
            obj.edit(config)

        result["changed"] = True
        result["repo"] = obj.raw_data

        return result
