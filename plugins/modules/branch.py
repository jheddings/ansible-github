"""Manage Github branch."""

from dataclasses import dataclass
from typing import Optional

from ansible.module_utils.basic import AnsibleModule

from github import GithubException
from github.Branch import Branch
from github.GithubException import UnknownObjectException

from ..module_utils.ghutil import GithubObjectConfig, ghconnect


@dataclass
class BranchConfig(GithubObjectConfig):
    name: str

    protected: Optional[bool] = None


class ModuleWrapper:
    def __init__(self, repo, token=None, org=None, base_url=None):
        owner = ghconnect(token, organization=org, base_url=base_url)

        # maintain a reference to the repository for branch operations
        self.repo = owner.get_repo(name=repo)

    def get(self, name) -> Branch:
        branch = None

        try:
            branch = self.repo.get_branch(name)
        except UnknownObjectException:
            return None

        return branch

    def absent(self, name, check_mode=False):
        branch = self.get(name=name)

        if branch is None:
            return {"changed": False}

        if not check_mode:
            raise NotImplementedError()

        return {"changed": True}

    def present(self, config: BranchConfig, check_mode=False):
        raise NotImplementedError()

    def default(self, config: BranchConfig, check_mode=False):
        raise NotImplementedError()


def run(params, check_mode=False):
    state = params.pop("state")

    mod = ModuleWrapper(
        token=params.pop("access_token", None),
        org=params.pop("organization", None),
        repo=params.pop("repository"),
        base_url=params.pop("api_url", None),
    )

    cfg = BranchConfig(**params)

    if state == "absent":
        result = mod.absent(cfg.name, check_mode=check_mode)

    elif state == "present":
        result = mod.present(cfg, check_mode=check_mode)

    elif state == "default":
        result = mod.default(cfg, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "access_token": {"type": "str", "no_log=": True},
        "organization": {"type": "str"},
        "repository": {"type": "str", "required": True},
        "api_url": {
            "type": "str",
            "default": "https://api.github.com",
        },
        "state": {
            "type": "str",
            "default": "present",
            "choices": ["present", "default", "absent"],
        },
        # label parameters
        "name": {"type": "str", "required": True},
        "protected": {"type": "bool"},
    }

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error: {err}")


if __name__ == "__main__":
    main()
