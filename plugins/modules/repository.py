"""Configure a Github repository."""

from dataclasses import dataclass
from typing import Optional

from github.GithubException import UnknownObjectException
from github.Repository import Repository

from ..module_utils.ghutil import GithubObjectConfig, ghconnect
from ..module_utils.runner import TaskRunner


@dataclass(eq=False)
class RepositoryConfig(GithubObjectConfig):
    """Configuration for github.Repository objects."""

    # the options here must be:
    #   a) supported by the API
    #   b) implemented by PyGithub
    #   c) handled correctly for create vs edit

    name: str
    description: Optional[str] = None
    private: Optional[bool] = None
    homepage: Optional[str] = None

    auto_init: Optional[bool] = None

    has_issues: Optional[bool] = None
    has_wiki: Optional[bool] = None
    has_projects: Optional[bool] = None
    has_downloads: Optional[bool] = None

    allow_merge_commit: Optional[bool] = None
    allow_squash_merge: Optional[bool] = None
    allow_rebase_merge: Optional[bool] = None

    delete_branch_on_merge: Optional[bool] = None

    # TODO support these parameters
    #   - default_branch
    #   - allow_auto_merge


class RepositoryManager:
    """Manage state of a Github repository."""

    def __init__(self, token=None, org=None, base_url=None):
        self.owner = ghconnect(token, organization=org, base_url=base_url)

    def get(self, name) -> Repository:
        """Get the named repository.

        If the repository does not exist, this method returns `None`.
        """
        repo = None

        try:
            repo = self.owner.get_repo(name=name)
        except UnknownObjectException:
            pass

        return repo

    def absent(self, name, check_mode=False):
        """Delete the named repository."""
        repo = self.get(name=name)

        if repo is None:
            return {"changed": False}

        if not check_mode:
            repo.delete()

        return {"changed": True}

    def archived(self, name, check_mode=False):
        """Archive the named repository."""
        repo = self.owner.get_repo(name=name)

        if not repo.archived:
            return {"changed": False}

        if not check_mode:
            repo.edit(archived=True)

        return {"changed": True}

    def present(self, config: RepositoryConfig, check_mode=False):
        """Ensure that the configured repository exists.

        If the repository does not exist, it will be created with the provided
        configuration.  If the repository exists, it will not be modified.
        """
        result = {"changed": False, "repo": None}

        repo = self.get(name=config.name)
        new_data = config.asdict()

        if repo is None:
            if not check_mode:
                repo = self.owner.create_repo(**new_data)

            result["changed"] = True

        result["repo"] = repo.raw_data

        return result

    def replace(self, config: RepositoryConfig, check_mode=False):
        """Replace the configuration of an existing repository.

        If the repository does not exist, it will be created.
        """
        result = {"changed": False, "repo": None}

        repo = self.get(name=config.name)
        new_data = config.asdict()

        if repo is None:
            if not check_mode:
                repo = self.owner.create_repo(**new_data)

            result["changed"] = True

        if config != repo:
            # remove create-only parameters
            new_data.pop("auto_init", None)

            if not check_mode:
                repo.edit(**new_data)

            result["changed"] = True

        result["repo"] = repo.raw_data

        return result


class RepositoryRunner(TaskRunner):
    """Runner for the jheddings.github.repository task."""

    def apply(self, state, params, check_mode=False):
        mgr = RepositoryManager(
            token=params.pop("access_token", None),
            org=params.pop("organization", None),
            base_url=params.pop("api_url", None),
        )

        cfg = RepositoryConfig(**params)

        if state == "absent":
            result = mgr.absent(cfg.name, check_mode=check_mode)

        elif state == "archived":
            result = mgr.archived(cfg.name, check_mode=check_mode)

        elif state == "replace":
            result = mgr.replace(cfg, check_mode=check_mode)

        elif state == "present":
            result = mgr.present(cfg, check_mode=check_mode)

        return result


def main():
    """Main module entry point."""

    runner = RepositoryRunner(
        # task parameters
        access_token={"type": "str", "no_log": True},
        organization={"type": "str"},
        api_url={
            "type": "str",
            "default": "https://api.github.com",
        },
        state={
            "type": "str",
            "default": "present",
            "choices": [
                "present",
                "replace",
                "absent",
                "archived",
            ],
        },
        # repo parameters
        name={"type": "str", "required": True},
        description={"type": "str"},
        homepage={"type": "str"},
        private={"type": "bool"},
        has_issues={"type": "bool"},
        has_downloads={"type": "bool"},
        has_wiki={"type": "bool"},
        has_projects={"type": "bool"},
        allow_merge_commit={"type": "bool"},
        allow_squash_merge={"type": "bool"},
        allow_rebase_merge={"type": "bool"},
        delete_branch_on_merge={"type": "bool"},
        # create parameters
        auto_init={"type": "bool"},
    )

    runner()


if __name__ == "__main__":
    main()
