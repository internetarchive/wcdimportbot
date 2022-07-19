import logging
from os.path import exists

from pydantic import BaseModel, validate_arguments

logger = logging.getLogger(__name__)


class WcdBaseModel(BaseModel):
    """This base model has all methods that we
    want to use in more than one class"""

    @validate_arguments
    def __log_to_file__(self, message: str, file_name: str) -> None:
        if not exists(file_name):
            with open(file_name, "x"):
                pass
        with open(file_name, "a") as f:
            f.write(f"{message}\n")
