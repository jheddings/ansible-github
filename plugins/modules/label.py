"""Configure a Github repository label."""

from ansible.module_utils.basic import AnsibleModule

from github import Github, GithubException
from github.GithubException import UnknownObjectException
from github.Label import Label
from github.Repository import Repository

from ..module_utils.mixin import GithubObjectMixin


class GithubWrapper(GithubObjectMixin):
    def __init__(self, repo: Repository):
        self.repo = repo

    @classmethod
    def connect(cls, repo_name, organization=None, token=None, base_url=None):
        if not base_url:
            return None

        client = Github(base_url=base_url, login_or_token=token)
        owner = (
            client.get_organization(organization) if organization else client.get_user()
        )
        repo = owner.get_repo(name=repo_name)

        return cls(repo=repo)

    def get(self, name) -> Label:
        label = None

        try:
            label = self.repo.get_label(name=name)
        except UnknownObjectException:
            return None

        return label

    def absent(self, name, check_mode=False):
        label = self.get(name=name)

        if label is None:
            return {"changed": False}

        if not check_mode:
            label.delete()

        return {"changed": True}

    def present(self, config, check_mode=False):
        result = {"changed": False, "label": None}

        label = self.get(name=config["name"])

        if label is None:
            if check_mode:
                result["label"] = config

            else:
                label = self.repo.create_label(**config)
                result["label"] = label.raw_data

            result["changed"] = True

        else:
            result = self.edit(label, config, check_mode=check_mode)

        return result


def run(params, check_mode=False):
    repo_name = params.pop("repository", None)
    token = params.pop("access_token", None)
    org = params.pop("organization", None)
    api_url = params.pop("api_url", None)
    state = params.pop("state")

    gh = GithubWrapper.connect(
        repo_name=repo_name,
        organization=org,
        token=token,
        base_url=api_url,
    )

    if state == "absent":
        result = gh.absent(params, check_mode=check_mode)

    elif state == "present":
        result = gh.present(params, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "repository": {"type": "str", "required": True},
        "access_token": {"type": "str", "no_log=": True},
        "organization": {"type": "str", "required": False, "default": None},
        "api_url": {
            "type": "str",
            "required": False,
            "default": "https://api.github.com",
        },
        "state": {
            "type": "str",
            "required": False,
            "default": "present",
            "choices": ["present", "absent"],
        },
        # label parameters
        "name": {"type": "str", "required": True},
        "color": {"type": "str", "required": True},
        "description": {"type": "str"},
    }

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error: {err}")


if __name__ == "__main__":
    main()
