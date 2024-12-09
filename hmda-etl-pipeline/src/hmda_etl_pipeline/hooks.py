import datetime
import logging
import re

from kedro.framework.context import KedroContext
from kedro.framework.hooks import hook_impl
from kedro.pipeline.node import Node
from .mattermost_notifier import post_mm_message
from typing import Any

# Used for date and time formats
timezone = datetime.timezone.utc
time_format = "%Y-%m-%dT%H:%M:%S%z"


class ProjectHooks:

    def __init__(self):
        self.mattermost_url = ""
        self.data_conf_catalog = {}
        self.post_to_mm = True
        self.post_to_mm_verbose = False

    @property
    def _logger(self):
        return logging.getLogger(__name__)

    @hook_impl
    def after_context_created(
        self,
        context: KedroContext,
    ) -> None:
        """Hooks to be invoked after a `KedroContext` is created.
        This is the earliest hook triggered within a Kedro run. The `KedroContext`
        stores useful information such as `credentials`, `config_loader` and `env`.

        Args:
            context: The context that was created.
        """

        if context.env != "local":
            # Turn off Mattermost posts for all hooks
            # Default is Mattermost posts for a few hooks
            if "post_to_mm" in context.params and context.params["post_to_mm"] == False:
                self.post_to_mm = False

            # Turn on Mattermost posts for all hooks
            if (
                "post_to_mm_verbose" in context.params
                and context.params["post_to_mm_verbose"] == True
            ):
                self.post_to_mm_verbose = True

        # Get Mattermost url from the params list of config map
        if "mm_url" in context.params:
            self.mattermost_url = context.params["mm_url"]
        elif "mm_url" in context.config_loader._globals:
            self.mattermost_url = context.config_loader._globals["mm_url"]
        else:
            # Mattermost url not provided, so turn off mattermost posts
            self.post_to_mm = False
            self.post_to_mm_verbose = False

    @hook_impl
    def after_catalog_created(self, conf_catalog: dict[str, Any]) -> None:
        """Hooks to be invoked after a data catalog is created.
        It receives the ``catalog`` as well as all the arguments for
        ``KedroContext._create_catalog``.

        Args:
            conf_catalog: The config from which the catalog was created.
        """

        # Get the data conf catalog
        self.data_conf_catalog = conf_catalog

    @hook_impl
    def before_node_run(self, node: Node) -> None:
        """Hook to be invoked before a node runs.
        The arguments received are the same as those used by ``kedro.runner.run_node``.

        Posts a message in mattermost before a node is run.

        Args:
            node (Node): The node to run
        """

        # Get current date and time
        date_and_time = datetime.datetime.now(tz=timezone).strftime(time_format)

        # Post message in mattermost
        msg = f"Starting kedro node {node.name} at {date_and_time}"
        if self.post_to_mm_verbose:
            post_mm_message(self.mattermost_url, msg)
        self._logger.info(msg)

    @hook_impl
    def after_node_run(self, node: Node) -> None:
        """Hook to be invoked after a node runs.

        The arguments received are the same as those used by ``kedro.runner.run_node``
        as well as the ``outputs`` of the node run.

        Posts a message in mattermost after a node is run.

        Args:
            node (Node): The node that ran
        """

        # Get current date and time
        date_and_time = datetime.datetime.now(tz=timezone).strftime(time_format)

        # Post message in mattermost
        msg = f"Finished running kedro node {node.name} at {date_and_time}"
        if self.post_to_mm_verbose:
            post_mm_message(self.mattermost_url, msg)
        self._logger.info(msg)

    @hook_impl
    def after_dataset_saved(self, dataset_name: str, data: Any, node: Node) -> None:
        """Hook to be invoked after a dataset is saved in the catalog.

        Posts a message in mattermost with the full path of the dataset and the
        row count for the dataset.

        Args:
            dataset_name: name of the dataset that was saved to the catalog.
            data: the actual data that was saved to the catalog.
            node: The ``Node`` that ran.
        """

        # Only post to mattermost if the node is tagged to be in data_publisher
        # pipeline and it not a row count or parquet dataset but the full dataset.
        if "data_publisher" in node.tags and not (
            "row_count" in dataset_name or "parquets" in dataset_name
        ):

            # Get current date and time
            date_and_time = datetime.datetime.now(tz=timezone).strftime(time_format)

            # Get the dataset template name
            matches = re.match(r"(\w+)(\d{4})(?:_q(\d))?", dataset_name)
            dataset_name_prefix = matches.group(1)
            year = matches.group(2)
            quarter = matches.group(3)
            
            dataset_template_name = dataset_name_prefix + "{year}"
            if quarter != None:
                dataset_template_name = dataset_template_name + "_q{quarter}"

            # Get dataset filepath using the data catalog
            dsconf = self.data_conf_catalog[dataset_template_name]
            dataset_filepath = (
                (
                    dsconf.get("filepath")
                    if dsconf.get("filepath")
                    else dsconf.get("path")
                )
                .replace("{year}", year)
                .replace("{quarter}", str(quarter))
            )

            # Create message
            msg = f"Pushed {dataset_filepath} at {date_and_time}"

            # Post message in mattermost
            if self.post_to_mm or self.post_to_mm_verbose:
                post_mm_message(self.mattermost_url, msg)
            self._logger.info(msg)

    @hook_impl
    def on_node_error(self, error: Exception, node: Node):
        """Hook to be invoked if a node run throws an uncaught error.
        The signature of this error hook should match the signature of ``before_node_run``
        along with the error that was raised.

        Posts a message in mattermost with the error encountered while running the node.

        Args:
            error: The uncaught exception thrown during the node run.
            node: The node to run.
        """

        # Post message to mattermost
        msg = f"Encountered error when running kedro node {node.name}: {error}"
        if self.post_to_mm or self.post_to_mm_verbose:
            post_mm_message(self.mattermost_url, msg)
        self._logger.error(msg)
