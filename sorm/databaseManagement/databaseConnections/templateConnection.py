from abc import ABC, abstractmethod
from email import generator
from typing import Generator
from ..utils import Condition

# Base class that is solely used to interface with the database
class DataBaseConnection(ABC):
    """ Base class for all DatabaseConnection classes"""
    _connection = None
    _connectionSettings = None

    @classmethod
    @abstractmethod
    def set_connection(cls:object, connectionSettings: dict) -> None:
        """ This method sets the class attribute _connection. 
        It should take a dictionary of connection settings and use them to connect to the database.
        It is called by the class method set_connection in the BaseManager class.
        """
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def _get_cursor(cls:object) -> object:
        """ This method returns a cursor object.
        """
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def get_fields(cls:object, table_name: str) -> list:
        """ This method returns a list of the fields in the table.
        """
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def select(cls:object, table_name:str, *field_names:tuple, chunk_size:int=2000, condition=None) -> Generator:  
        """ This method selects data from the database and returns a generator of rows.
        It can be used to SELECT * FROM table_name or SELECT field1, field2, ... FROM table_name.
        It can also be used to SELECT ____ FROM table_name WHERE condition.
        The generator yields the rows in chunks of size chunk_size.
        """
        raise NotImplementedError
     
    @classmethod
    @abstractmethod
    def insert(cls:object, table_name:str, **row_data:dict) -> None:
        """ This method inserts a row into the database.
        It takes the table name and keyword arguments of the form field_name=value
        """
        raise NotImplementedError
       
    @classmethod
    @abstractmethod
    def update(cls:object, table_name:str, dataToChange: dict, condition:Condition) -> None:
        """ This method updates rows in the database where the condition is met.
        It takes the table name, a dictionary of the form field_name=new_value, and a Condition object."""
        raise NotImplementedError 
    
    @classmethod
    @abstractmethod
    def get_last_row_id(cls:object) -> int:
        """ This method returns the id of the last row inserted into the database."""
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def delete(cls:object, table_name:str, condition:Condition) -> None:
        """ This method deletes rows in the database where the condition is met.
        It takes the table name and a Condition object."""
        raise NotImplementedError