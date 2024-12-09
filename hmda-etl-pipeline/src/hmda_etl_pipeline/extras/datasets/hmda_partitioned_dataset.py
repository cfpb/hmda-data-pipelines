"""``HMDAPartitionedDataset`` loads and saves partitioned file-like data using the
underlying dataset definition. It also uses `fsspec` for filesystem level operations.
"""

from __future__ import annotations

from datetime import datetime
from copy import deepcopy
import pytz
from typing import Any, Dict
from urllib.parse import urlparse

from kedro.io.core import AbstractDataset

from kedro.io.data_catalog import CREDENTIALS_KEY
from kedro_datasets.partitions import PartitionedDataset

S3_PROTOCOLS = ("s3", "s3a", "s3n")


class HMDAPartitionedDataset(PartitionedDataset):
    def __init__(  # noqa: too-many-arguments
        self,
        path: str,
        dataset: str | type[AbstractDataset] | dict[str, Any],
        filepath_arg: str = "filepath",
        filename_suffix: str = "",
        credentials: dict[str, Any] = None,
        load_args: dict[str, Any] = None,
        fs_args: dict[str, Any] = None,
        overwrite: bool = False,
        metadata: Dict[str, Any] = None,
    ):
        """Creates a new instance of ``PartitionedDataset``.

        Args:
            path: Path to the folder containing partitioned data.
                If path starts with the protocol (e.g., ``s3://``) then the
                corresponding ``fsspec`` concrete filesystem implementation will
                be used. If protocol is not specified,
                ``fsspec.implementations.local.LocalFileSystem`` will be used.
                **Note:** Some concrete implementations are bundled with ``fsspec``,
                while others (like ``s3`` or ``gcs``) must be installed separately
                prior to usage of the ``PartitionedDataset``.
            dataset: Underlying dataset definition. This is used to instantiate
                the dataset for each file located inside the ``path``.
                Accepted formats are:
                a) object of a class that inherits from ``AbstractDataset``
                b) a string representing a fully qualified class name to such class
                c) a dictionary with ``type`` key pointing to a string from b),
                other keys are passed to the Dataset initializer.
                Credentials for the dataset can be explicitly specified in
                this configuration.
            filepath_arg: Underlying dataset initializer argument that will
                contain a path to each corresponding partition file.
                If unspecified, defaults to "filepath".
            filename_suffix: If specified, only partitions that end with this
                string will be processed.
            credentials: Protocol-specific options that will be passed to
                ``fsspec.filesystem``
                https://filesystem-spec.readthedocs.io/en/latest/api.html#fsspec.filesystem
                and the dataset initializer. If the dataset config contains
                explicit credentials spec, then such spec will take precedence.
                All possible credentials management scenarios are documented here:
                https://kedro.readthedocs.io/en/stable/data/kedro_io.html#partitioned-dataset-credentials
            load_args: Keyword arguments to be passed into ``find()`` method of
                the filesystem implementation.
            fs_args: Extra arguments to pass into underlying filesystem class constructor
                (e.g. `{"project": "my-project"}` for ``GCSFileSystem``)
            overwrite: If True, any existing partitions will be removed.
            metadata: Any arbitrary metadata.
                This is ignored by Kedro, but may be consumed by users or external plugins.

        Raises:
            DatasetError: If versioning is enabled for the underlying dataset.
        """

        self._path = path

        super().__init__(
            path=path,
            dataset=dataset,
            filepath_arg=filepath_arg,
            filename_suffix=filename_suffix,
            credentials=credentials,
            load_args=load_args,
            fs_args=fs_args,
            overwrite=overwrite,
            metadata=metadata,
        )

    def _describe(self) -> Dict[str, Any]:
        clean_dataset_config = (
            {k: v for k, v in self._dataset_config.items() if k != CREDENTIALS_KEY}
            if isinstance(self._dataset_config, dict)
            else self._dataset_config
        )
        return {
            "path": self._path,
            "dataset_type": self._dataset_type.__name__,
            "dataset_config": clean_dataset_config,
        }

    def _normalized_save_path(self, path: str) -> str:
        if self._protocol in S3_PROTOCOLS:
            return urlparse(path)._replace(scheme="s3").geturl()
        return path

    def _partition_to_path(self, path: str, filename: str):
        dir_path = path.rstrip(self._sep)
        filename = filename.lstrip(self._sep)
        full_path = self._sep.join([dir_path, filename]) + self._filename_suffix
        return full_path

    def _save(self, data: dict[str, Any]) -> None:
        normalized_path = self._normalized_save_path(self._path)

        if self._overwrite and self._filesystem.exists(normalized_path):
            self._filesystem.rm(normalized_path, recursive=True)

        date = datetime.strftime(
            datetime.now(pytz.timezone("America/New_York")), r"%Y-%m-%d"
        )
        path_latest = self._path
        path_dated = path_latest.replace("latest", date)

        for partition_id, partition_data in sorted(data.items()):
            kwargs = deepcopy(self._dataset_config)

            # Save to latest directory
            partition = self._partition_to_path(path_latest, partition_id)
            # join the protocol back since tools like PySpark may rely on it
            kwargs[self._filepath_arg] = self._join_protocol(partition)
            dataset = self._dataset_type(**kwargs)  # type: ignore
            if callable(partition_data):
                partition_data = partition_data()  # noqa: redefined-loop-name
            dataset.save(partition_data)

            # Save to dated directory
            partition_dated = self._partition_to_path(path_dated, partition_id)
            kwargs[self._filepath_arg] = self._join_protocol(partition_dated)
            dataset_dated = self._dataset_type(**kwargs)  # type: ignore
            if callable(partition_data):
                partition_data = partition_data()  # noqa: redefined-loop-name
            dataset_dated.save(partition_data)

        self._invalidate_caches()
