"""
Test the Condition class
"""
import pytest

@pytest.mark.dependency()
def test_condition():
    from sorm.databaseManagement.utils import Condition
    x = Condition(id=1)
    assert x is not None
    assert x.sql_format == 'id = ?'
    assert x.query_vars == [1]