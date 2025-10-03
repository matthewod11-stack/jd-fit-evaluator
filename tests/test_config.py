import pytest
from pydantic import ValidationError
from jd_fit_evaluator.config import EmbeddingConfig

def test_invalid_batch_size():
    with pytest.raises(ValidationError):
        EmbeddingConfig(batch_size=0)