"""
Excel Formatter for AutoLabo reports.

Centralizes all Excel format creation and conditional format selection.
Formats are created once in __init__ and reused throughout the export.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ExcelFormatter:
    """
    Manages Excel cell formats for AutoLabo reports.
    
    Creates all formats upfront during initialization to avoid
    repeated format creation in loops (performance optimization).
    
    Usage:
        formatter = ExcelFormatter(workbook)
        fmt = formatter.get_header_format('green')
        cond_fmt = formatter.get_conditional_format('sols', value, limits)
    """
    
    # Color mapping for headers
    HEADER_COLORS = {
        'gray': '#D9D9D9',
        'green': '#C6EFCE',
        'orange': '#FBCA98',
        'white': '#FFFFFF',
        'pink': '#FFCCFF',
        'cyan': '#CCFFFF',
        'yellow': '#FFFF99',
        'red': '#FF99CC',
    }
    
    # Conditional format colors
    COND_COLORS = {
        'green': '#C6EFCE',
        'yellow': '#FFE699',
        'orange': '#FBCA98',
        'isdd': '#FFFFFF',  # White bg, red font
        'isdnd': '#FF99CC',
        'isdi_plus': '#FFFF99',
        'isdi': '#CCFFFF',
        'hcsp': '#FFCCFF',
    }
    
    def __init__(self, workbook):
        """
        Initialize formatter and create all formats.
        
        Args:
            workbook: xlsxwriter.Workbook instance
        """
        self.workbook = workbook
        self._formats: Dict[str, Any] = {}
        self._create_all_formats()
        logger.debug("ExcelFormatter initialized with all formats")
    
    def _create_all_formats(self) -> None:
        """Create all formats upfront."""
        # Header formats
        for color_name, color_hex in self.HEADER_COLORS.items():
            self._formats[f'header_{color_name}'] = self.workbook.add_format({
                'bold': True,
                'bg_color': color_hex,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'text_wrap': True
            })
        
        # Standard cell formats
        self._formats['param'] = self.workbook.add_format({
            'border': 1,
            'align': 'left'
        })
        
        self._formats['center'] = self.workbook.add_format({
            'border': 1,
            'align': 'center'
        })
        
        self._formats['family'] = self.workbook.add_format({
            'bold': True,
            'bg_color': '#0070C0',
            'font_color': 'white',
            'border': 1
        })
        
        # Conditional formats - Eaux
        self._formats['cond_green'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['green']
        })
        
        self._formats['cond_yellow'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['yellow']
        })
        
        self._formats['cond_orange'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['orange']
        })
        
        # Conditional formats - Sols
        self._formats['cond_isdd_exceeded'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': '#FFFFFF',
            'font_color': 'red'
        })
        
        self._formats['cond_isdnd'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['isdnd']
        })
        
        self._formats['cond_isdi_plus'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['isdi_plus']
        })
        
        self._formats['cond_isdi'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['isdi']
        })
        
        self._formats['cond_hcsp'] = self.workbook.add_format({
            'border': 1,
            'align': 'center',
            'bg_color': self.COND_COLORS['hcsp'],
            'font_color': 'red'
        })
        
        # Legend format
        self._formats['legend_text'] = self.workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'font_size': 9
        })
    
    def get_format(self, name: str) -> Any:
        """Get a format by name."""
        return self._formats.get(name, self._formats['center'])
    
    def get_header_format(self, color: str) -> Any:
        """
        Get header format by color name.
        
        Args:
            color: Color name (green, orange, white, pink, cyan, yellow, red)
            
        Returns:
            xlsxwriter format object
        """
        key = f'header_{color}'
        return self._formats.get(key, self._formats['header_gray'])
    
    def get_conditional_format_eaux(
        self, 
        value: Optional[float], 
        limits: Dict[str, float],
        col_color_map: Dict[str, str]
    ) -> Any:
        """
        Get conditional format for Eaux based on regulatory thresholds.
        
        Args:
            value: Parsed numeric value
            limits: Dict of {column_key: limit_value}
            col_color_map: Dict of {column_key: color_name}
            
        Returns:
            Format for the cell
        """
        if value is None:
            return self._formats['center']
        
        matched_color = None
        
        for limit_col, limit_val in limits.items():
            if value >= limit_val:
                color = col_color_map.get(limit_col, 'green')
                if color == 'orange':
                    matched_color = 'orange'
                elif color == 'yellow' and matched_color != 'orange':
                    matched_color = 'yellow'
                elif color == 'green' and matched_color is None:
                    matched_color = 'green'
        
        if matched_color == 'orange':
            return self._formats['cond_orange']
        elif matched_color == 'yellow':
            return self._formats['cond_yellow']
        elif matched_color == 'green':
            return self._formats['cond_green']
        
        return self._formats['center']
    
    def get_conditional_format_sols(
        self, 
        value: Optional[float], 
        limits: Dict[str, float]
    ) -> Any:
        """
        Get conditional format for Sols based on ISDI/ISDI+/ISDND/ISDD thresholds.
        
        Args:
            value: Parsed numeric value
            limits: Dict of {column_key: limit_value}
            
        Returns:
            Format for the cell
        """
        if value is None:
            return self._formats['center']
        
        # Regulatory column indices for Sols
        limit_isdd = limits.get('16_REF')
        limit_isdnd = limits.get('14_REF')
        limit_isdi_plus = limits.get('13_REF')
        limit_isdi = limits.get('11_REF')
        limit_hcsp_dep = limits.get('10_REF')
        
        if limit_isdd is not None and value >= limit_isdd:
            return self._formats['cond_isdd_exceeded']
        elif limit_isdnd is not None and value >= limit_isdnd:
            return self._formats['cond_isdnd']
        elif limit_isdi_plus is not None and value >= limit_isdi_plus:
            return self._formats['cond_isdi_plus']
        elif limit_isdi is not None and value >= limit_isdi:
            return self._formats['cond_isdi']
        elif limit_hcsp_dep is not None and value >= limit_hcsp_dep:
            return self._formats['cond_hcsp']
        
        return self._formats['center']
    
    def create_legend_format(self, bg_color: str, font_color: str = 'black') -> Any:
        """
        Create a custom format for legend items.
        
        Args:
            bg_color: Background color (hex)
            font_color: Font color name
            
        Returns:
            New format object
        """
        return self.workbook.add_format({
            'bg_color': bg_color,
            'border': 1,
            'text_wrap': True,
            'valign': 'vcenter',
            'font_color': font_color
        })
