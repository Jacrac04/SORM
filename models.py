import uuid
from db import db


def uuidGen():
    return str(uuid.uuid4())


def generate_password_hash(password, method=None):
    return password

class PythonDataAuthTokens(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    authToken = db.Field('authToken', data_type='varchar')
    tokenType = db.Field('tokenType', data_type='varchar')
    pythonDataId = db.ForeignKey('python_data.id')
    pythonData = db.Relationship('PythonData', 'authTokens')

    def __init__(self, tokenType, pythonDataId):
        self.authToken = uuidGen()
        self.tokenType = tokenType
        self.pythonDataId = pythonDataId

class PythonData(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    name = db.Field('name', data_type='varchar')
    dataJson = db.Field('dataJson', data_type='varchar')
    authTokens = db.Relationship('PythonDataAuthTokens', 'pythonData')
    projectId = db.ForeignKey('project.id')
    project = db.Relationship('Project', "pythonData")
    pass


class Project(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    name = db.Field('name', data_type='varchar')
    description = db.Field('description', data_type='varchar')
    # pythonDataId = db.ForeignKey('python_data.id')
    # backref='Project', lazy='dynamic')
    pythonData = db.Relationship('PythonData', 'project')
    ownerId = db.ForeignKey('user.id')
    owner = db.Relationship('User', 'projects')
    pass

    def __init__(self, name, ownerId, description):
        self.name = name
        self.ownerId = ownerId
        self.description = description
        
class User(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    email = db.Field('email', data_type='varchar')
    password = db.Field('password', data_type='varchar')
    name = db.Field('name', data_type='varchar')
    admin = db.Field('admin', data_type='boolean')
    projects = db.Relationship('Project', 'owner')
    
    def __init__(self, email, password, name, admin=False):
        self.email = email
        self.password = self._generate_password_hash(password)
        self.name = name
        self.admin = admin
    
    @staticmethod
    def _generate_password_hash (password_plaintext: str):
        return generate_password_hash(password_plaintext, method='sha256')
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_admin(self):
        return self.admin

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.name



    