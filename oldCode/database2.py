
from dataclasses import fields
import re
import sqlite3
import itertools
import sqlite3
from tkinter.tix import COLUMN
from oldCode.utils import Blank, Field, ForeignKeyField, NewRelationship,  ForeignKey, Relationship, InstrumentedAttribute, F, Condition, InstrumentedAttributeRelationship
import re
from abc import ABC, abstractmethod


# Base class that is solely used to interface with the database
class DataBaseConnection(ABC):
    @classmethod
    @abstractmethod
    def set_connection(cls, connectionSettings: dict) -> None:
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def _get_cursor(cls):
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def get_fields(cls, table_name: str) -> list:
        raise NotImplementedError
    
    @classmethod
    @abstractmethod
    def select(cls, table_name, *field_names, chunk_size=2000, condition=None) -> list:
        raise NotImplementedError
     
    @classmethod
    @abstractmethod
    def insert(cls, **row_data):
        raise NotImplementedError
       
    @classmethod
    @abstractmethod
    def update(cls, dataToChange:dict, id:int) -> None:
        raise NotImplementedError 
        
class SQLITEBaseConnection(DataBaseConnection):
    @classmethod
    def set_connection(cls, connectionSettings: dict) -> None:    
        cls._connectionSettings = connectionSettings
        cls._connection = sqlite3.connect(connectionSettings['databaseURI'], isolation_level=connectionSettings['isolation_level'])
        cls._cursor = cls._connection.cursor()
        cls._cursor.execute("PRAGMA foreign_keys = ON")
        cls._connection.commit()
    
    @classmethod
    def _get_cursor(cls):
        return cls._cursor
    
    @classmethod
    def get_fields(cls, table_name):
        cls._cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cls._cursor.fetchall()]
    
    @classmethod
    def select(cls, table_name, *field_names, chunk_size=2000, condition=None):
        if not field_names:
            field_names = '*' # cls.get_fields(table_name)
        if condition:
            cls._cursor.execute(f"SELECT {', '.join(field_names)} FROM {table_name} WHERE {condition.sql_format}", condition.query_vars)
        else:
            cls._cursor.execute(f"SELECT {', '.join(field_names)} FROM {table_name}")
        fetching_complete = False
        while not fetching_complete:
            rows = cls._cursor.fetchmany(size=chunk_size)
            for row in rows:
                yield row
            fetching_complete = len(rows) < chunk_size
    
    @classmethod
    def insert(cls, table_name, **row_data):
        query = f"INSERT INTO {table_name} ({', '.join(row_data.keys())}) VALUES ({', '.join(['?'] * len(row_data))})"
        cls._cursor.execute(query, tuple(row_data.values()))
        
    @classmethod
    def update(cls, table_name, dataToChange: dict, condition) -> None:
        query = f"UPDATE {table_name} SET {', '.join([f'{field} = ?' for field in dataToChange.keys()])} WHERE {condition}"
        cls._cursor.execute(query, tuple(dataToChange.values()))
    
    @classmethod
    def get_last_row_id(cls):
        return cls._cursor.lastrowid
          
class NewBaseManager:
    connection = None
    connection_options = {'SQLITE': SQLITEBaseConnection}
    
    @classmethod
    def set_connection(cls, connectionSettings: dict) -> None:
        cls.connection = cls.connection_options[connectionSettings['type']]
        cls.connection.set_connection(connectionSettings)
    
    def __init__(self, model_class):
        self.model_class = model_class
        
    @property
    def table_name(self):
        x = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model_class.table_name).lower()
        return x
        
    def filter_by(self, **kwargs):
        condition = Condition(**kwargs)
        model_objects = self.select('*', condition=condition)
        return model_objects

    
    
    def select(self, *field_names, chunk_size=2000, condition=None):
        if '*' in field_names:
            rows = self.connection.select(self.table_name, chunk_size=chunk_size, condition=condition)
            field_names = self.connection.get_fields(self.table_name)
        else:
            rows = self.connection.select(self.table_name, *field_names, chunk_size=chunk_size, condition=condition)
        model_objects = []
        for row in rows:
            row_data = dict(zip(field_names, row))
            x = Blank() # Create a blank object
            self.model_class.__bases__[0].__init__(x, new_record=False,**row_data) # Call the parent init on the blank object
            x.__class__ = self.model_class 
            # model_objects.append(self.model_class(new_record=False,**row_data))
            model_objects.append(x) 
        return model_objects
    
    def bulk_insert(self, data):
        field_names = self.connection.get_fields(self.table_name)
        for row in data:
            assert row.keys() == field_names
        self.connection.insert(self.table_name, **data) 
        
    def insert(self, **row_data):
        self.bulk_insert(data=[row_data])      
    
    def update(self, dataToChange: dict, condition) -> None:
        self.connection.update(self.table_name, dataToChange, condition.sql_format)   
        
    def updateOne(self, dataToChange: dict, id:int) -> None:
        self.connection.update(self.table_name, dataToChange, f"id = {id}")
        
    def delete(self, condition) -> None:
        pass
    
    def newRecord(self, data):
        self.connection.insert(self.table_name, **data)
        return self.connection.get_last_row_id()
            

def testfunc(string1:str):
    return exec()



def _wrapCustomInit(baseInit, self, data):
    result = baseInit(*self, **data)
    pk = self[0].__class__.primary_key
    self[0].__dict__[pk] = self[0].__class__.query.newRecord(data)
    return result

class MetaModel(type):
    manager_class = NewBaseManager
    models = {}

        

    def __new__(cls, name, bases, attrs):
        inst = super().__new__(cls, name, bases, attrs)
        inst.manager = cls._get_manager(cls)
        inst.foreign_keys = {}
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        inst.table_name = name
        for attr in attrs:
            x = None
            childcls = None
            string1 = None
            string2 = None
            if (attr.startswith('_') and not attr.startswith('__init_')) or (not attr.startswith('__init_') and (not (isinstance(attrs[attr], Field) or isinstance(attrs[attr], Relationship) or isinstance(attrs[attr], NewRelationship) or isinstance(attrs[attr], ForeignKey)))):
                continue
            elif isinstance(attrs[attr], Field):
                if attrs[attr].primary_key:
                    inst.primary_key = attr
                x = InstrumentedAttribute(attrs[attr].name, attrs[attr].data_type, attrs[attr].primary_key)
            elif isinstance(attrs[attr], Relationship):
                y = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].parentcls)).lower()
                z = attrs[attr].back_populates
                print(attr, attrs[attr], attrs[attr].parentcls, attrs[attr].back_populates, re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].parentcls)).lower())
                x = property(fget=lambda self: MetaModel.models[y].query.filter_by(**{z:self.id}))
            elif isinstance(attrs[attr], NewRelationship):
                childcls = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].childcls)).lower()
                if attrs[attr].back_populates:
                    print(attrs[attr])
                    string1 = re.sub(r'(?<!^)(?=[A-Z])', '_', (str(attrs[attr].childcls))).lower()+ ".id"
                    string2 = re.sub(r'(?<!^)(?=[A-Z])', '_', (inst.__name__)).lower()
                    # print(string1, string2)
                    def fget(self, string1=string1, string2=string2, childcls=childcls):
                        if string1 in MetaModel.models[string2].foreign_keys:
                            return MetaModel.models[childcls].query.filter_by(**{'id':getattr(self, self.foreign_keys[string1])})[0]
                        else:
                            return MetaModel.models[childcls].query.filter_by(**{MetaModel.models[childcls].foreign_keys[re.sub(r'(?<!^)(?=[A-Z])', '_', (str(self.__class__.__name__))).lower()+ ".id"]:self.id})
                    def fset(self, value, string1=string1, string2=string2, childcls=childcls):
                        print(self, value, string1, string2, childcls)
                        if string1 in MetaModel.models[string2].foreign_keys:
                            attr_name = self.foreign_keys[string1]
                            attr_obj = getattr(self, attr_name)
                            if not childcls == value.__class__.__name__.lower():
                                raise ValueError(f"Can't set {childcls} to a {value.__class__.__name__.lower()}")
                            setattr(self, attr_name, value.id)
                            
                    x = property(fget=lambda self, string1=string1, string2=string2, childcls=childcls: 
                        # func(self, string1, string2, childcls))
                        MetaModel.models[childcls].query.filter_by(**{'id':getattr(self, self.foreign_keys[string1])})[0]
                        if string1 in MetaModel.models[string2].foreign_keys else
                        MetaModel.models[childcls].query.filter_by(**{MetaModel.models[childcls].foreign_keys[re.sub(r'(?<!^)(?=[A-Z])', '_', (str(self.__class__.__name__))).lower()+ ".id"]:self.id}),
                        fset=fset)
                    # x = property(fget=lambda self: MetaModel.models[childcls].query.filter_by(**{attrs[attr].back_populates:self.id}))
                else: 
                    x = property(fget=lambda self, childcls=childcls: MetaModel.models[childcls].query.filter_by(**{MetaModel.models[childcls].foreign_keys[str(self.__class__.__name__).lower()+ ".id"]:self.id}))
            elif isinstance(attrs[attr], ForeignKey):
                x = InstrumentedAttribute(attr, 'int', False)
                inst.foreign_keys[attrs[attr].key] = attr
                    
                    
            elif attr == '__init__':
                if name != 'base_model':
                    x = lambda *args, **kwargs: _wrapCustomInit(attrs[attr], args, kwargs)
                else:
                    continue
            setattr(inst, attr, x)
            # print(string1, string2, childcls, x)
            pass
        MetaModel.models[name] = inst
        return inst
    
    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def query(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    table_name = ""

    def __init__(self, new_record=True, **data):
        self.initialized = False
        if new_record:
            # id = self.__class__.query.newRecord(data)
            pk = self.__class__.primary_key
            pkdata = self.__class__.query.newRecord(data)
            data.update({pk:pkdata})
        for field_name, value in data.items():
            setattr(self, field_name, value)
        self.initialized = True
 

    def __repr__(self):
        attrs_format = ", ".join([f'{field}={value}' for field, value in self.__dict__.items()])
        return f"<{self.__class__.__name__}: ({attrs_format})>"

    @classmethod
    def get_fields(cls):
        return cls._get_manager()._get_fields()
        
class ORM():
    def __init__(self):
        self.Model = BaseModel
        self.session = NewBaseManager
        connectionSettings = {
            'type': 'SQLITE',
            'databaseURI': 'dev.sqlite',
            'isolation_level': None
        }  
        self.session.set_connection(connectionSettings)
        self.__setFields()
        
    def __setFields(self):
        self.Field = Field
        self.ForeignKeyField = ForeignKeyField
        self.Relationship = Relationship
        self.NewRelationship = NewRelationship
        self.ForeignKey = ForeignKey
        
        
