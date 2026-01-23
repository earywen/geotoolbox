"""
Excel writer module for laboratory reports.

This module provides the core scaffolding for generating Excel workbooks
from processed laboratory data.
"""

import logging
from io import BytesIO
from typing import Dict, Any, List
import pandas as pd
import xlsxwriter

from ..config.models import MatrixConfig

logger = logging.getLogger(__name__)


class ExcelWriter:
    """
    Handles Excel workbook generation for laboratory reports.

    This class provides the infrastructure for creating Excel files,
    managing workbooks and worksheets. The actual formatting and content
    writing is delegated to specialized modules (formatter, legend).
    """

    def __init__(self, config: MatrixConfig, samples: List[Dict[str, Any]]):
        """
        Initialize the Excel writer.

        Args:
            config: Matrix configuration with formatting rules
            samples: List of detected samples (name, date, idx)
        """
        self.config = config
        self.samples = samples

    def generate_excel(
        self,
        df_merged: pd.DataFrame,
        formats_dict: Dict[str, Any],
        header_writer_fn,
        data_writer_fn,
        legend_writer_fn
    ) -> BytesIO:
        """
        Generate the complete Excel report.

        This is the main orchestration method that creates the workbook,
        delegates writing to specialized functions, and returns the output.

        Args:
            df_merged: Merged DataFrame with all data
            formats_dict: Dictionary of xlsxwriter formats
            header_writer_fn: Function to write headers
            data_writer_fn: Function to write data rows
            legend_writer_fn: Function to write legend

        Returns:
            BytesIO containing the Excel file
        """
        logger.info("Generating Excel report...")

        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet("Rapport")

        # Write headers
        current_row = header_writer_fn(worksheet, formats_dict)

        # Write data
        current_row = data_writer_fn(worksheet, df_merged, formats_dict, current_row)

        # Write legend
        legend_writer_fn(worksheet, workbook, current_row + 2)

        workbook.close()
        output.seek(0)

        logger.info("Excel report generated successfully")
        return output
