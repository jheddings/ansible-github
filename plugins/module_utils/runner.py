"""Common utilities for custom modules."""

from abc import ABC, abstractmethod

from ansible.module_utils.basic import AnsibleModule
from github import GithubException


class TaskRunner(ABC):
    def __init__(self, **spec):
        self.module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    @abstractmethod
    def apply(self, state, params=None, check_mode=False):
        """Apply the requested state."""

    def __call__(self):
        params = self.module.params
        check_mode = self.module.check_mode

        state = params.pop("state")

        try:
            result = self.apply(state, params=params, check_mode=check_mode)
            self.module.exit_json(**result)
        except GithubException as err:
            self.module.fail_json(msg=f"Github Error [{err.status}]: {err.data}")
