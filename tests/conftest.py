import pytest
from tests.confIntergrationTests import IntergrationTestData   
        
    
@pytest.fixture(scope="module")
def sorm():
    yield IntergrationTestData.db

@pytest.fixture(scope="module")
def userModel():
    yield IntergrationTestData.User
    
@pytest.fixture(scope="module")
def projectModel():
    yield IntergrationTestData.Project
    
@pytest.fixture(scope="module")
def dataModel():
    yield IntergrationTestData.PythonData

@pytest.fixture(scope="module")
def pythonDataAuthTokensModel():
    yield IntergrationTestData.PythonDataAuthTokens

@pytest.fixture(scope="module")
def sqlConnection():
    from sorm.databaseManagement.databaseConnections.sqliteConn import SQLITEBaseConnection
    SETTINGS = {
                'type': 'SQLITE',
                'databaseURI': 'testing.sqlite',
                'isolation_level': 'DEFERRED',
                'commit': True
            }
    conn = SQLITEBaseConnection()
    yield conn