"""
These tests test SQLITEBaseConnection from sorm.databaseManagement.databaseManagement.sqliteConn
"""
import pytest


@pytest.mark.dependency()
def test_sqlite_connection():
    from sorm.databaseManagement.databaseConnections.sqliteConn import SQLITEBaseConnection
    SETTINGS = {
                'type': 'SQLITE',
                'databaseURI': 'testing.sqlite',
                'isolation_level': 'DEFERRED'
            }
    conn = SQLITEBaseConnection()
    conn.set_connection(SETTINGS)
    assert conn is not None
 
@pytest.mark.dependency(depends=["test_sqlite_connection"])   
def test_sqlite_select(sqlConnection):
    resp = sqlConnection.select('test_sql_database')
    assert resp is not None
    resp = list(resp)
    assert resp == [(1, 'Test 1', 1), (2, 'Test 2', 2)]
    
    resp = sqlConnection.select('test_sql_database', 'name')
    assert resp is not None
    resp = list(resp)
    assert resp == [('Test 1',), ('Test 2',)]
    
    from sorm.databaseManagement.utils import Condition
    resp = sqlConnection.select('test_sql_database', condition=Condition(id=1))
    assert resp is not None
    resp = list(resp)
    assert resp == [(1, 'Test 1', 1)]
   
    
@pytest.mark.dependency(depends=["test_sqlite_connection", "test_sqlite_select"])
def test_sqlite_insert(sqlConnection):
    sqlConnection.insert('test_sql_database', **{'name': 'Test 3', 'value': 3})
    resp = sqlConnection.get_last_row_id()
    assert resp == 3
    
    resp = sqlConnection.select('test_sql_database')
    assert resp is not None
    resp = list(resp)
    assert (3, 'Test 3', 3) in resp
    
    sqlConnection._cursor.execute('DELETE FROM test_sql_database WHERE id = 3')

# "test_sqlite_connection", "test_sqlite_select",
@pytest.mark.dependency(depends=["tests/unit/test_sql_connections.py::test_sqlite_connection", "tests/unit/test_sql_connections.py::test_sqlite_select", "tests/unit/test_databaseManagement_utils.py::test_condition"], scope='session')
def test_sqlite_update(sqlConnection):
    from sorm.databaseManagement.utils import Condition
    sqlConnection.update('test_sql_database', {'name': 'Test 2.2'}, condition=Condition(id=2))
    resp = sqlConnection.select('test_sql_database')
    assert resp is not None
    resp = list(resp)
    assert (2, 'Test 2.2', 2) in resp
    
    sqlConnection.update('test_sql_database', {'name': 'Test 2'}, condition=Condition(id=2))
    resp = sqlConnection.select('test_sql_database')
    assert resp is not None
    resp = list(resp)
    assert (2, 'Test 2', 2) in resp


@pytest.mark.dependency(depends=["test_sqlite_connection"])
def test_get_fields(sqlConnection):
    resp = sqlConnection.get_fields('test_sql_database')
    assert resp == ['id', 'name', 'value']
    