"""Configure secrets for a Github repository."""

from dataclasses import dataclass

from ..module_utils.ghutil import GithubObjectConfig, ghconnect
from ..module_utils.runner import TaskRunner


@dataclass(eq=False)
class SecretsConfig(GithubObjectConfig):
    """Configuration for secrets."""

    name: str
    value: str | None = None


class SecretsManager:
    """Manage secrets in a Github repository."""

    def __init__(self, repo, token=None, org=None, base_url=None):
        owner = ghconnect(token, organization=org, base_url=base_url)
        self.repo = owner.get_repo(name=repo)

    def absent(self, name):
        """Delete a secret."""

        if self.repo.delete_secret(secret_name=name):
            return {"changed": True}

        return {"changed": False}

    def present(self, name, value):
        """Create a secret.

        Since secrets are encrypted, we cannot check if the secret already exists.  As
        a result, this method will always return `changed: True` on success.
        """

        if self.repo.create_secret(secret_name=name, unencrypted_value=value):
            return {"changed": True, "name": name}

        return {"changed": False, "name": name}


class SecretsRunner(TaskRunner):
    """Runner for the jheddings.github.label task."""

    def apply(self, state, params, check_mode=False):
        if check_mode:
            raise ValueError("check_mode is not supported for this module")

        mod = SecretsManager(
            token=params.pop("access_token", None),
            org=params.pop("organization", None),
            repo=params.pop("repository"),
            base_url=params.pop("api_url", None),
        )

        cfg = SecretsConfig(**params)

        if state == "absent":
            return mod.absent(cfg.name)

        if state == "present":
            return mod.present(cfg.name, cfg.value)

        raise ValueError(f"unknown state: {state}")


def main():
    """Main module entry point."""

    runner = SecretsRunner(
        # task parameters
        access_token={"type": "str", "no_log": True},
        organization={"type": "str"},
        repository={"type": "str", "required": True},
        api_url={
            "type": "str",
            "default": "https://api.github.com",
        },
        state={
            "type": "str",
            "default": "present",
            "choices": [
                "present",
                "absent",
            ],
        },
        # secrets parameters
        name={"type": "str", "required": True},
        value={"type": "str"},
    )

    runner()


if __name__ == "__main__":
    main()
