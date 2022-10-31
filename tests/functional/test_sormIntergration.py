"""
SORM was originally designed to be in one of my projects (https://github.com/Jacrac04/PythonDataStoreServer), but I decided to make it a separate project.
These are the tests for the SORM integration with the project.
"""
import pytest

@pytest.mark.dependency()
def test_user_query(userModel):
    x = userModel.query.filter_by(id=2)[0]
    assert x.id == 2
    assert x.email == 'test@test.com'
    assert x.name == 'Test User'
    assert x.admin == False    

@pytest.mark.dependency()
def test_project_query(projectModel):
    project = projectModel.query.filter_by(id=1)[0]
    assert project.id == 1
    assert project.name == 'Test Project'
    assert project.ownerId == 2
    assert project.description == 'Test Description'

@pytest.mark.dependency()
def test_data_query(dataModel):
    data = dataModel.query.filter_by(id=1)[0]
    assert data.id == 1
    assert data.name == 'Test Data'
    assert data.dataJson == '{"test": "test"}'
    assert data.projectId == 1

@pytest.mark.dependency()
def test_authToken_query(pythonDataAuthTokensModel):
    authToken = pythonDataAuthTokensModel.query.filter_by(id=1)[0]
    assert authToken.id == 1
    assert authToken.authToken == 'testAuthToken'
    assert authToken.tokenType == 'r'
    assert authToken.pythonDataId == 1

@pytest.mark.dependency(depends=["test_user_query", "test_project_query"])
def test_user_to_project_relationship(projectModel):
    project = projectModel.query.filter_by(id=1)[0]
    assert project.owner.id == 2

@pytest.mark.dependency(depends=["test_project_query", "test_data_query"])
def test_project_to_data_relationship(dataModel):
    data = dataModel.query.filter_by(id=1)[0]
    assert data.project.id == 1

@pytest.mark.dependency(depends=["test_data_query", "test_authToken_query"])   
def test_data_to_authToken_relationship(pythonDataAuthTokensModel):
    authToken = pythonDataAuthTokensModel.query.filter_by(id=1)[0]
    assert authToken.pythonData.id == 1