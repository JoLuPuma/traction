"""Profile manager for multitenancy."""
import inspect
import os
import logging

from aries_cloudagent.config.settings import BaseSettings
from aries_cloudagent.config.injector import BaseInjector
from aries_cloudagent.config.base import InjectionError
from aries_cloudagent.utils.classloader import ClassLoader, ClassNotFoundError

from aries_cloudagent.multitenant.manager_provider import MultitenantManagerProvider

LOGGER = logging.getLogger(__name__)


class CustomMultitenantManagerProvider(MultitenantManagerProvider):

    config_key = "multitenant_provider"

    def __init__(self, root_profile):
         super().__init__(root_profile)
         self.manager_class = None

    def get_config(self, settings: BaseSettings):
        try:
            plugin_config = settings["plugin_config"] or {}
            config = plugin_config[self.config_key]
            return config
        except KeyError as error:
            # will just proceed with defaults
            LOGGER.warning(f"No configuration section found for plugin '{self.config_key}'.")
            return {}    

    def get_manager_class(self, config: dict):
        try:
            return config["manager_class"]
        except KeyError as error:
            LOGGER.warning(f"No configuration found for '{self.config_key}.manager_class', proceeding with default.")
            return "multitenant_provider.manager.BasicMultitokenMultitenantManager"     
        

    def provide(self, settings: BaseSettings, injector: BaseInjector):
        """Create the multitenant manager instance."""

        if not self.manager_class:
            # we have not loaded a manager...
            config = self.get_config(settings)
            manager_class = self.get_manager_class(config)
            LOGGER.info(f"Create multitenant manager (class={manager_class})")
            try:
                self._inst[manager_class] = ClassLoader.load_class(manager_class)(
                    self.root_profile
                )
                self.manager_class = manager_class
            except ClassNotFoundError as err:
                raise InjectionError(
                    f"Error loading multitenant manager, class '{manager_class}' not found."
                ) from err

        # return our loaded manager class...
        return self._inst[self.manager_class]
