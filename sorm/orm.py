from .modelManagement import BaseModel, Field, ForeignKey, NewRelationship, NewBaseManager
from .fields.fields import ForeignKeyField, Relationship 

class ORM():
    def __init__(self, connectionSettings):
        self.Model = BaseModel
        self.session = NewBaseManager
        self.session.set_connection(connectionSettings)
        self.__setFields()
        
    def __setFields(self):
        self.Field = Field
        self.ForeignKeyField = ForeignKeyField
        self.Relationship = Relationship
        self.NewRelationship = NewRelationship
        self.ForeignKey = ForeignKey