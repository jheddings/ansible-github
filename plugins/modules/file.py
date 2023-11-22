"""Manage a Github repository file."""

# https://pygithub.readthedocs.io/en/latest/examples/Repository.html#get-a-specific-content-file

from dataclasses import dataclass
from typing import Any, Optional

from github.ContentFile import ContentFile
from github.GithubException import UnknownObjectException
from github.GithubObject import NotSet

from ..module_utils.ghutil import GithubObjectConfig, ghconnect
from ..module_utils.runner import TaskRunner


@dataclass(eq=False)
class FileConfig(GithubObjectConfig):
    path: str
    message: str

    content: Optional[Any] = None
    source: Optional[str] = None

    def __eq__(self, other):
        """Compare the current configuration to another object.

        If the other object is a `ContentFile`, this method uses the file path and
        raw contents to determine equality
        """
        if isinstance(other, ContentFile):
            return all(
                [
                    self.path == other.path,
                    self.content == other.decoded_content,
                ]
            )

        return super().__eq__(other)

    def __post_init__(self):
        """Verify configuration options."""

        # if the caller provided source, load into content instead
        if self.source is not None:
            with open(self.source, "rb") as fp:
                self.content = fp.read()

            self.source = ...


class FileManager:
    """Manage files in a Github repository."""

    def __init__(self, repo, branch=None, token=None, org=None, base_url=None):
        owner = ghconnect(token, organization=org, base_url=base_url)
        self.repo = owner.get_repo(name=repo)
        self.ref = NotSet if branch is None else branch

    def get(self, path) -> ContentFile:
        """Get the requested file from this manager.

        If the file does not exist, this method returns `None`.
        """
        file = None

        try:
            file = self.repo.get_contents(path=path, ref=self.ref)
        except UnknownObjectException:
            return None

        # TODO make sure we have a single file type

        return file

    def absent(self, config: FileConfig, check_mode=False):
        """Delete the file using the configuration provided."""
        file = self.get(path=config.path)

        if file is None:
            return {"changed": False, "message": None}

        if not check_mode:
            self.repo.delete_file(file.path, config.message, file.sha, branch=self.ref)

        return {"changed": True, "message": config.message}

    def present(self, config: FileConfig, update=False, check_mode=False):
        """Ensure that the configured file exists.

        If the file does not exist, it will be created based on the provided
        configuration.  If the file exists, it will be modified to match the
        given configuration if requested.
        """
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

    def replace(self, config: FileConfig, check_mode=False):
        """Replace the configuration of an existing file.

        If the file does not exist, it will be created.
        """
        return self.present(config, update=True, check_mode=check_mode)


class FileRunner(TaskRunner):
    """Runner for the jheddings.github.label task."""

    def apply(self, state, params, check_mode=False):
        mgr = FileManager(
            token=params.pop("access_token", None),
            org=params.pop("organization", None),
            repo=params.pop("repository"),
            branch=params.pop("branch", None),
            base_url=params.pop("api_url", None),
        )

        cfg = FileConfig(**params)

        if state == "absent":
            result = mgr.absent(cfg, check_mode=check_mode)

        elif state == "present":
            result = mgr.present(cfg, check_mode=check_mode)

        elif state == "replace":
            result = mgr.replace(cfg, check_mode=check_mode)

        return result


def main():
    """Main module entry point."""

    runner = FileRunner(
        # task parameters
        access_token={"type": "str", "no_log": True},
        organization={"type": "str"},
        repository={"type": "str", "required": True},
        branch={"type": "str"},
        api_url={
            "type": "str",
            "default": "https://api.github.com",
        },
        state={
            "type": "str",
            "default": "present",
            "choices": ["present", "replace", "absent"],
        },
        # file parameters
        path={"type": "str", "required": True},
        message={"type": "str", "required": True},
        content={"type": "raw"},
        source={"type": "str"},
    )

    runner()


if __name__ == "__main__":
    main()
