from abc import ABC, abstractmethod
from oldCode.utils import Condition

# Base class that is solely used to interface with the database
class DataBaseConnection(ABC):
    _conection = None
    _connectionSettings = None

    @classmethod
    @abstractmethod
    def set_connection(cls:object, connectionSettings: dict) -> None:
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def _get_cursor(cls:object) -> object:
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def get_fields(cls:object, table_name: str) -> list:
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def select(cls:object, table_name:str, *field_names:tuple, chunk_size:int=2000, condition=None) -> list:  
        raise NotImplementedError
     
    @classmethod
    @abstractmethod
    def insert(cls:object, table_name:str, **row_data:dict) -> None:
        raise NotImplementedError
       
    @classmethod
    @abstractmethod
    def update(cls:object, table_name:str, dataToChange: dict, condition:Condition) -> None:
        raise NotImplementedError 
    
    @classmethod
    @abstractmethod
    def get_last_row_id(cls:object) -> int:
        raise NotImplementedError