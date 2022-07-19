import logging
from typing import Any, Optional

import pyssdb  # type: ignore
from pydantic import validate_arguments

from src.wcd_base_model import WcdBaseModel

logger = logging.getLogger(__name__)


class SsdbDatabase(WcdBaseModel):
    """Class modeling the SSDB database

    SSDB has an auth command for authentication but
    we don't use it because it is sent in clear text and that is pretty useless"""

    port: int = 8888  # "6379"
    host: str = "127.0.0.0"
    # host: str = "archive-wcd.aws.scatter.red"
    connection: Optional[Any]

    def connect(self):
        try:
            self.connection = pyssdb.Client(
                host=self.host,
                port=self.port,
            )
        except ConnectionRefusedError as e:
            raise ConnectionRefusedError(
                f"Could not connect to the AWS SSDB cache, got {e}"
            )

    @validate_arguments
    def delete(self, key: str):
        if self.connection is not None:
            return self.connection.delete(key)
        else:
            raise ValueError("self.connection was None")

    def flush_database(self):
        logger.info("Flushing the SSDB database now")
        if self.connection is not None:
            return self.connection.flushdb()
        else:
            raise ValueError("self.connection was None")

    def get_info(self):
        return self.connection.info()

    @validate_arguments
    def get_value(self, key: str):
        if self.connection is not None:
            return self.connection.get(key)
        else:
            raise ValueError("self.connection was None")

    @validate_arguments
    def set_value(self, key: str, value: str):
        logger.debug("set_value: Running")
        if self.connection is not None:
            return self.connection.set(key, value)
        else:
            raise ValueError("self.connection was None")
