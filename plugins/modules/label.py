"""Configure a Github repository label."""

from dataclasses import dataclass

from ansible.module_utils.basic import AnsibleModule

from github import GithubException
from github.GithubException import UnknownObjectException
from github.Label import Label

from ..module_utils.mixin import GithubObjectConfig, ghconnect


@dataclass
class LabelConfig(GithubObjectConfig):
    name: str
    color: str = ...
    description: str = ...


class ModuleWrapper:
    def __init__(self, repo_name, token=None, organization=None, base_url=None):
        owner = ghconnect(token, organization=organization, base_url=base_url)

        # maintain a reference to the repository for label operations
        self.repo = owner.get_repo(name=repo_name)

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

    def present(self, config: LabelConfig, check_mode=False):
        result = {"changed": False, "label": None}

        label = self.get(name=config.name)
        new_data = config.asdict()

        if label is None:
            result["changed"] = True

            if not check_mode:
                label = self.repo.create_label(**new_data)

        elif config != label:
            result["changed"] = True

            if not check_mode:
                result = label.edit(**new_data)

        result["label"] = label.raw_data

        return result


def run(params, check_mode=False):
    state = params.pop("state")

    mod = ModuleWrapper(
        token=params.pop("access_token", None),
        organization=params.pop("organization", None),
        repo_name=params.pop("repository"),
        base_url=params.pop("api_url", None),
    )

    if state == "absent":
        result = mod.absent(params["name"], check_mode=check_mode)

    elif state == "present":
        result = mod.present(params, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "access_token": {"type": "str", "no_log=": True},
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
        "organization": {
            "type": "str",
            "required": False,
            "default": None,
        },
        "repository": {"type": "str", "required": True},
        "name": {"type": "str", "required": True},
        "color": {
            "type": "str",
            "required": False,
            "default": "cccccc",
        },
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
