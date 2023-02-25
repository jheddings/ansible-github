"""Manage Github repository collaorators."""

from dataclasses import dataclass

from ..module_utils.ghutil import GithubObjectConfig, ghconnect
from ..module_utils.runner import TaskRunner


@dataclass(eq=False)
class CollaboratorConfig(GithubObjectConfig):
    """Configuration for collaborators."""

    username: str
    permission: str


class CollaboratorManager:
    """Manage collaborators in a Github repository."""

    def __init__(self, repo, token=None, org=None, base_url=None):
        owner = ghconnect(token, organization=org, base_url=base_url)
        self.repo = owner.get_repo(name=repo)

    def absent(self, name, check_mode=False):
        """Remove the collaborator from the repository."""
        if not self.repo.has_in_collaborators(name):
            return {"changed": False}

        if not check_mode:
            self.repo.remove_from_collaborators(name)

        return {"changed": True}

    def present(self, config: CollaboratorConfig, check_mode=False):
        """Ensure that the collaaborator exists with the specified permissions."""
        result = {"changed": False, "username": config.username, "permission": None}

        perm = None

        if self.repo.has_in_collaborators(config.username):
            perm = self.repo.get_collaborator_permission(config.username)

        if perm != config.permission:
            result["changed"] = True

            if not check_mode:
                self.repo.add_to_collaborators(config.username, config.permission)

        result["permission"] = perm

        return result


class CollaboratorRunner(TaskRunner):
    """Runner for the jheddings.github.collaborator task."""

    def apply(self, state, params, check_mode=False):
        mod = CollaboratorManager(
            token=params.pop("access_token", None),
            org=params.pop("organization", None),
            repo=params.pop("repository"),
            base_url=params.pop("api_url", None),
        )

        cfg = CollaboratorConfig(**params)

        if state == "absent":
            result = mod.absent(cfg.username, check_mode=check_mode)

        elif state == "present":
            result = mod.present(cfg, check_mode=check_mode)

        return result


def main():
    """Main module entry point."""

    runner = CollaboratorRunner(
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
        # collaborator parameters
        username={"type": "str", "required": True},
        permission={
            "type": "str",
            "default": "push",
            "choices": [
                "pull",
                "triage",
                "push",
                "maintain",
                "admin",
            ],
        },
    )

    runner()


if __name__ == "__main__":
    main()
