import pytest
import pandas as pd
from io import BytesIO
from modules.autolabo_core.processors.base import BaseProcessor

def test_base_processor_cannot_be_instantiated():
    """Verify that BaseProcessor cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseProcessor("raw", "ref")

def test_concrete_subclass_must_implement_abstract_methods():
    """Verify that subclasses must implement abstract methods."""
    class IncompleteProcessor(BaseProcessor):
        def process(self):
            pass
        # Missing validate
    
    with pytest.raises(TypeError):
        IncompleteProcessor("raw", "ref")

def test_concrete_subclass_instantiation():
    """Verify valid subclass instantiation."""
    class CompleteProcessor(BaseProcessor):
        def process(self) -> BytesIO:
            return BytesIO()
        
        def validate(self, df: pd.DataFrame) -> bool:
            return True
            
    processor = CompleteProcessor("raw", "ref")
    assert isinstance(processor, BaseProcessor)
    assert processor.validate(pd.DataFrame()) is True
