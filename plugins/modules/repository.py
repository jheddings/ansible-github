"""Configure a Github repository."""

from typing import Union

from ansible.module_utils.basic import AnsibleModule

from github import Github, GithubException
from github.AuthenticatedUser import AuthenticatedUser
from github.GithubException import UnknownObjectException
from github.GithubObject import GithubObject
from github.Organization import Organization
from github.Repository import Repository


class GithubWrapper:
    def __init__(self, owner: Union[AuthenticatedUser, Organization]):
        self.owner = owner

    @classmethod
    def connect(cls, organization=None, token=None, base_url=None):
        if not base_url:
            return None

        client = Github(base_url=base_url, login_or_token=token)
        owner = (
            client.get_organization(organization) if organization else client.get_user()
        )

        return cls(owner=owner)

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

    def present(self, config, check_mode=False):
        result = {"changed": False, "repo": None}

        repo = self.get(name=config["name"])

        if repo is None:
            if check_mode:
                result["repo"] = config

            else:
                repo = self.owner.create_repo(**config)
                result["repo"] = repo.raw_data

            result["changed"] = True

        else:
            result = self.edit(repo, config, check_mode=check_mode)

        return result

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
            obj.edit(**config)

        result["changed"] = True
        result["repo"] = obj.raw_data

        return result


def run(params, check_mode=False):
    token = params.pop("access_token", None)
    org = params.pop("organization", None)
    api_url = params.pop("api_url", None)
    state = params.pop("state")

    gh = GithubWrapper.connect(
        organization=org,
        token=token,
        base_url=api_url,
    )

    if state == "absent":
        result = gh.absent(params["name"], check_mode=check_mode)

    elif state == "archived":
        result = gh.archived(params["name"], check_mode=check_mode)

    elif state == "present":
        result = gh.present(params, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "access_token": {"type": "str", "no_log=": True},
        "organization": {"type": "str", "required": False, "default": None},
        "name": {"type": "str", "required": True},
        "api_url": {
            "type": "str",
            "required": False,
            "default": "https://api.github.com",
        },
        "state": {
            "type": "str",
            "required": False,
            "default": "present",
            "choices": ["present", "absent", "archived"],
        },
        # repo parameters
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
    }

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error: {err}")


if __name__ == "__main__":
    main()
