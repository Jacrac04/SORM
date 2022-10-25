from .modelManagement import BaseModel, Field, ForeignKey, NewBaseManager
from .fields.fields import Relationship 

class ORM():
    def __init__(self, connectionSettings):
        self.Model = BaseModel
        self.session = NewBaseManager
        self.session.set_connection(connectionSettings)
        self.__setFields()
        
    def __setFields(self):
        self.Field = Field
        self.Relationship = Relationship
        self.ForeignKey = ForeignKey