"""Configure a Github repository."""

from ansible.module_utils.basic import AnsibleModule

from github import Github, GithubException
from github.ContentFile import ContentFile
from github.GithubException import UnknownObjectException
from github.GithubObject import NotSet
from github.Repository import Repository


class GithubWrapper:
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

    def get(self, name, ref=NotSet) -> ContentFile:
        contents = None

        try:
            contents = self.repo.get_contents(name, ref=ref)
        except UnknownObjectException:
            return None

        return contents

    def absent(self, filename, branch=NotSet, check_mode=False):
        file = self.get(name=filename)

        if file is None:
            return {"changed": False, "file": filename}

        if not check_mode:
            self.repo.delete_file(file.path, "remove test", file.sha, branch=branch)

        return {"changed": True, "file": file.path}

    def present(self, config, check_mode=False):
        result = {"changed": False, "file": None}

        return result


def run(params, check_mode=False):
    token = params.pop("access_token", None)
    org = params.pop("organization", None)
    api_url = params.pop("api_url", None)
    state = params.pop("state")
    repo = params.pop("repository")

    gh = GithubWrapper.connect(
        organization=org,
        token=token,
        repo_name=repo,
        base_url=api_url,
    )

    filename = params.pop("branch")
    branch = params.pop("branch", None)

    if state == "absent":
        result = gh.absent(filename, branch, check_mode=check_mode)

    elif state == "present":
        result = gh.present(
            filename, branch, content=params["content"], check_mode=check_mode
        )

    return result


def main():
    """Main module entry point."""

    spec = {
        # task parameters
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
        # file parameters
        "repository": {"type": "str", "required": True},
        "filename": {"type": "str", "required": True},
        "content": {"type": "str", "required": True},
        "branch": {"type": "str"},
        "commit_message": {"type": "str"},
    }

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    try:
        result = run(module.params, module.check_mode)
        module.exit_json(**result)
    except GithubException as err:
        module.fail_json(msg=f"Github Error: {err}")


if __name__ == "__main__":
    main()
