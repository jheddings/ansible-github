"""Configure a Github repository."""

from dataclasses import dataclass
from typing import Optional

from ansible.module_utils.basic import AnsibleModule

from github import GithubException
from github.GithubException import UnknownObjectException
from github.Repository import Repository

from ..module_utils.ghutil import GithubObjectConfig, ghconnect


@dataclass
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


class ModuleWrapper:
    def __init__(self, token=None, org=None, base_url=None):
        self.owner = ghconnect(token, organization=org, base_url=base_url)

    def get(self, name) -> Repository:
        repo = None

        try:
            repo = self.owner.get_repo(name=name)
        except UnknownObjectException:
            pass

        return repo

    def absent(self, name, check_mode=False):
        repo = self.get(name=name)

        if repo is None:
            return {"changed": False}

        if not check_mode:
            repo.delete()

        return {"changed": True}

    def archived(self, name, check_mode=False):
        repo = self.owner.get_repo(name=name)

        if not repo.archived():
            return {"changed": False}

        if not check_mode:
            repo.edit(archived=True)

        return {"changed": True}

    def present(self, config: RepositoryConfig, check_mode=False):
        result = {"changed": False, "repo": None}

        repo = self.get(name=config.name)
        new_data = config.asdict()

        if repo is None:
            result["changed"] = True

            if not check_mode:
                repo = self.owner.create_repo(**new_data)

        elif config != repo:
            result["changed"] = True

            # remove create-only parameters
            new_data.pop("auto_init", None)

            if not check_mode:
                result = repo.edit(**new_data)

        result["repo"] = repo.raw_data

        return result


def run(params, check_mode=False):
    state = params.pop("state")

    mod = ModuleWrapper(
        token=params.pop("access_token", None),
        org=params.pop("organization", None),
        base_url=params.pop("api_url", None),
    )

    lbl = RepositoryConfig(**params)

    if state == "absent":
        result = mod.absent(lbl.name, check_mode=check_mode)

    elif state == "archived":
        result = mod.archived(lbl.name, check_mode=check_mode)

    elif state == "present":
        result = mod.present(lbl, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "access_token": {"type": "str", "no_log=": True},
        "organization": {"type": "str"},
        "api_url": {
            "type": "str",
            "default": "https://api.github.com",
        },
        "state": {
            "type": "str",
            "default": "present",
            "choices": ["present", "absent", "archived"],
        },
        # repo parameters
        "name": {"type": "str", "required": True},
        "description": {"type": "str"},
        "homepage": {"type": "str"},
        "private": {"type": "bool"},
        "has_issues": {"type": "bool"},
        "has_downloads": {"type": "bool"},
        "has_wiki": {"type": "bool"},
        "has_projects": {"type": "bool"},
        "allow_merge_commit": {"type": "bool"},
        "allow_squash_merge": {"type": "bool"},
        "allow_rebase_merge": {"type": "bool"},
        "delete_branch_on_merge": {"type": "bool"},
        # create only parameters
        "auto_init": {"type": "bool"},
    }

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error [{err.status}]: {err.data}")


if __name__ == "__main__":
    main()
