from .databaseConnections.templateConnection import DataBaseConnection
from .databaseConnections.sqliteConn import SQLITEBaseConnection
from .utils import Condition, Blank, SORMArray
import re
        
class BaseManager:
    """BaseManager class provides an interface to interact with the database.
    
    Class attributes:
        - connection: a DataBaseConnection object. This handles the actual SQL (or similar) commands.
        - connection_options: a dictionary of Connection options.  
    
    Class Methods:
        - set_connection: instantiates the connection to the database.
    
    Methods:
        - get_fields: returns a list of the fields in the table.
        - filter_by: returns a list of model objects that match the conditions.
        - select: returns a list of model objects that match the conditions.
        - bulk_insert: inserts a list of entries into the database.
        - insert: inserts an entry into the database.
        - update: updates entries that match a condition in the database .
        - updateOne: updates one entry in the database.
        - delete: deletes entries that match a condition from the database.
        - newRecord: creates a new entry in the database.

    """
    connection = DataBaseConnection # Refactor to a property that generates a new connection for request. 
    connection_options = {'SQLITE': SQLITEBaseConnection}
    
    @classmethod
    def set_connection(cls, connectionSettings: dict) -> None:
        cls.connection = cls.connection_options[connectionSettings['type']]
        cls.connection.set_connection(connectionSettings)
        print("Connection set", cls)
    
    def __init__(self, model_class) -> None:
        print("BaseManager init", self, self.connection,id(self.connection), model_class)
        self.model_class = model_class
        
    @property
    def table_name(self):
        x = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model_class.table_name).lower()
        return x
    
    def get_fields(self):
        return self.connection.get_fields(self.table_name)
        
    def filter_by(self, **kwargs):
        condition = Condition(**kwargs)
        model_objects = self.select('*', condition=condition)
        return model_objects

    
    def select(self, *field_names, chunk_size=2000, condition=None):
        # If the user wants all the fields, get them from the database.
        if '*' in field_names:
            rows = self.connection.select(self.table_name, chunk_size=chunk_size, condition=condition)
            field_names = self.connection.get_fields(self.table_name)
        else:
            # Otherwise, just get the fields that the user wants.
            rows = self.connection.select(self.table_name, *field_names, chunk_size=chunk_size, condition=condition)
        # Create a list to return
        model_objects = SORMArray()
        # Iterate through the rows and create a model object for each row.
        for row in rows:
            row_data = dict(zip(field_names, row))
            x = Blank() # Create a blank object
            self.model_class.__bases__[0].__init__(x, new_record=False,**row_data) # Call the parent init on the blank object
            x.__class__ = self.model_class   # type: ignore
            # Add the object to the model_objects list.
            model_objects.append(x) 
        # Return the list of model objects.
        return model_objects
    
    def bulk_insert(self, data: dict) -> None:
        field_names = self.connection.get_fields(self.table_name)
        for row in data:
            assert row.keys() == field_names
        self.connection.insert(self.table_name, **data) 
        
    def insert(self, **row_data: dict) -> None:
        self.bulk_insert(data=[row_data])      
    
    def update(self, dataToChange: dict, condition) -> None:
        self.connection.update(self.table_name, dataToChange, condition)   
        
    def updateOne(self, dataToChange: dict, id:int) -> None:
        self.connection.update(self.table_name, dataToChange, Condition(id=id))
        
    def delete(self, **kwargs) -> None:
        self.connection.delete(self.table_name, Condition(**kwargs))
    
    def newRecord(self, data):
        self.connection.insert(self.table_name, **data)
        return self.connection.get_last_row_id()