from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
from io import BytesIO

class BaseProcessor(ABC):
    """
    Abstract Base Class for all Laboratory Processors.

    This interface ensures consistency between legacy and new processors.
    """

    def __init__(self, raw_path: str, ref_path: str, config: Dict[str, Any] = None):
        """
        Initialize the processor.

        Args:
            raw_path: Path to the raw laboratory file.
            ref_path: Path to the reference file.
            config: Optional configuration dictionary.
        """
        self.raw_path = raw_path
        self.ref_path = ref_path
        self.config = config or {}

    @abstractmethod
    def process(self) -> BytesIO:
        """
        Execute the processing pipeline.

        Returns:
            BytesIO: The generated Excel file in memory.
        """
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate the structure of the input data.

        Args:
            df: The raw input dataframe.

        Returns:
            bool: True if valid, False otherwise.
        """
        pass
