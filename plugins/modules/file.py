"""Manage a Github repository file."""

# https://pygithub.readthedocs.io/en/latest/examples/Repository.html#get-a-specific-content-file

from dataclasses import dataclass
from typing import Any, Optional

from ansible.module_utils.basic import AnsibleModule

from github import GithubException
from github.ContentFile import ContentFile
from github.GithubException import UnknownObjectException
from github.GithubObject import NotSet

from ..module_utils.ghutil import GithubObjectConfig, ghconnect


@dataclass
class FileConfig(GithubObjectConfig):
    path: str
    message: str

    content: Optional[Any] = None

    def __eq__(self, other):
        if isinstance(other, ContentFile):
            return all(
                [
                    self.path == other.path,
                    self.content == other.decoded_content,
                ]
            )

        return super().__eq__(other)


class ModuleWrapper:
    def __init__(self, repo, branch=None, token=None, org=None, base_url=None):
        owner = ghconnect(token, organization=org, base_url=base_url)

        # maintain a reference to the repository for file operations
        self.repo = owner.get_repo(name=repo)

        self.ref = NotSet if branch is None else branch

    def get(self, path) -> ContentFile:
        file = None

        try:
            file = self.repo.get_contents(path=path, ref=self.ref)
        except UnknownObjectException:
            return None

        # TODO make sure we have a single file type

        return file

    def absent(self, config: FileConfig, check_mode=False):
        file = self.get(path=config.path)

        if file is None:
            return {"changed": False, "message": None}

        if not check_mode:
            self.repo.delete_file(file.path, config.message, file.sha, branch=self.ref)

        return {"changed": True, "message": config.message}

    def present(self, config: FileConfig, update=False, check_mode=False):
        result = {"changed": False, "file": None}

        file = self.get(path=config.path)

        if file is None:
            result["changed"] = True

            if not check_mode:
                created = self.repo.create_file(
                    config.path,
                    config.message,
                    config.content,
                    branch=self.ref,
                )
                file = created["content"]

        elif update and (config != file):
            result["changed"] = True

            if not check_mode:
                updated = self.repo.update_file(
                    config.path,
                    config.message,
                    config.content,
                    file.sha,
                    branch=self.ref,
                )
                file = updated["content"]

        result["file"] = file.raw_data

        return result


def run(params, check_mode=False):
    state = params.pop("state")

    mod = ModuleWrapper(
        token=params.pop("access_token", None),
        org=params.pop("organization", None),
        repo=params.pop("repository"),
        branch=params.pop("branch", None),
        base_url=params.pop("api_url", None),
    )

    # if the caller provided source, load into content instead

    src = params.pop("source", None)

    if src is not None:
        with open(src, "rb") as fp:
            params["content"] = fp.read()

    cfg = FileConfig(**params)

    # configure the desired state

    if state == "absent":
        result = mod.absent(cfg, check_mode=check_mode)

    elif state == "present":
        result = mod.present(cfg, check_mode=check_mode)

    elif state == "replace":
        result = mod.present(cfg, update=True, check_mode=check_mode)

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
        "access_token": {"type": "str", "no_log=": True},
        "organization": {"type": "str"},
        "repository": {"type": "str", "required": True},
        "branch": {"type": "str"},
        "api_url": {
            "type": "str",
            "default": "https://api.github.com",
        },
        "state": {
            "type": "str",
            "default": "present",
            "choices": ["present", "replace", "absent"],
        },
        # file parameters
        "path": {"type": "str", "required": True},
        "message": {"type": "str", "required": True},
        "content": {"type": "raw"},
        "source": {"type": "str"},
    }

    module = AnsibleModule(
        argument_spec=spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("content", "source"),
        ],
        required_if=[
            ("state", "present", ("source", "content"), True),
        ],
    )

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error: {err}")


if __name__ == "__main__":
    main()
