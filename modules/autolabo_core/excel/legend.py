"""
Excel legend module for laboratory reports.

This module handles legend generation including:
- Regulatory notes
- Color coding explanations
"""

import logging
from typing import Any

from ..config.models import LegendConfig

logger = logging.getLogger(__name__)


class LegendWriter:
    """
    Handles legend writing for laboratory reports.

    This class generates the legend section at the bottom of Excel reports,
    including notes and color-coded items explaining regulatory thresholds.
    """

    def __init__(self, legend_config: LegendConfig):
        """
        Initialize the legend writer.

        Args:
            legend_config: Legend configuration from MatrixConfig
        """
        self.legend_config = legend_config

    def write_legend(self, worksheet: Any, workbook: Any, start_row: int) -> None:
        """
        Write the legend section to the worksheet.

        Args:
            worksheet: xlsxwriter worksheet object
            workbook: xlsxwriter workbook object
            start_row: Starting row for the legend
        """
        current_row = start_row

        fmt_legend_text = workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'font_size': 9
        })

        # Write notes
        for note in self.legend_config.notes:
            if note:
                worksheet.merge_range(current_row, 0, current_row, 8, note, fmt_legend_text)
            current_row += 1

        current_row += 1

        # Write color legend items
        for item in self.legend_config.color_items:
            fmt_color = workbook.add_format({
                'bg_color': item.bg_color,
                'border': 1,
                'text_wrap': True,
                'valign': 'vcenter',
                'font_color': item.font_color
            })
            worksheet.merge_range(current_row, 0, current_row, 8, item.description, fmt_color)
            current_row += 1
