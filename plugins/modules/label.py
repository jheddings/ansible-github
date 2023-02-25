"""Configure a Github repository label."""

import re
from dataclasses import dataclass
from typing import Optional

from github.Label import Label

from ..module_utils.config import GithubObjectConfig
from ..module_utils.manager import ResourceManager
from ..module_utils.runner import TaskRunner

label_color_re = re.compile(r"^[0-9a-fA-F]{6}$")


@dataclass(eq=False)
class LabelConfig(GithubObjectConfig):
    """Configuration for github.Label objects."""

    name: str
    color: str = "cccccc"
    description: Optional[str] = None

    def __post_init__(self):
        if self.color is None:
            raise ValueError("'color' cannot be None")

        if not label_color_re.match(self.color):
            raise ValueError("'color' must be a valid hex color")


class LabelManager(ResourceManager):
    """Manage labels in a Github repository."""

    def __init__(self, token, name, repo, owner, base_url=None):
        super().__init__(token=token, base_url=base_url)

        self.owner = owner
        self.repo = repo
        self.name = name

    def get(self) -> Label:
        """Get the managed label from this manager."""
        return self.api.get(f"/repos/{self.owner}/{self.repo}/labels/{self.name}")

    def absent(self, check_mode=False):
        """Delete the named label."""
        label = self.get()

        if label is None:
            return {"changed": False}

        if not check_mode:
            label.delete()

        return {"changed": True}

    def present(self, config: LabelConfig, check_mode=False):
        """Ensure that the label configuration exists.

        If the label does not exist, it will be created based on the provided
        configuration.  If the label exists, it will be modified to match the
        given configuration.
        """
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
                label.edit(**new_data)

        result["label"] = label.raw_data

        return result


class LabelRunner(TaskRunner):
    """Runner for the jheddings.github.label task."""

    def apply(self, state, params, check_mode=False):
        mgr = LabelManager(
            token=params.pop("access_token", None),
            org=params.pop("organization", None),
            repo=params.pop("repository"),
            base_url=params.pop("api_url", None),
        )

        cfg = LabelConfig(**params)

        if state == "absent":
            result = mgr.absent(cfg.name, check_mode=check_mode)

        elif state == "present":
            result = mgr.present(cfg, check_mode=check_mode)

        return result


def main():
    """Main module entry point."""

    runner = LabelRunner(
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
        # label parameters
        name={"type": "str", "required": True},
        color={
            "type": "str",
            "default": "cccccc",
        },
        description={"type": "str"},
    )

    runner()


if __name__ == "__main__":
    main()
