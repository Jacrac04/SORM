
from dataclasses import fields
import re
import sqlite3
import itertools
import sqlite3
from tkinter.tix import COLUMN
from utils import Blank, Field, ForeignKeyField, NewRelationship,  ForeignKey, Relationship, InstrumentedAttribute, F, Condition, InstrumentedAttributeRelationship
from types import MethodType

import re

global func

def func(*x):
    print(x)

class BaseManager:
    connection = None

    @classmethod
    def set_connection(cls, database_settings):
        connection = sqlite3.connect("dev.sqlite", isolation_level=None)
        # connection.autocommit = True
        cls.connection = connection

    @classmethod
    def _get_cursor(cls):
        return cls.connection.cursor()
    
    @classmethod
    def _execute_query(cls, query, vars):
        cursor = cls._get_cursor()
        if vars:
            cursor.execute(query, vars)
        else:
            cursor.execute(query)

    def __init__(self, model_class):
        self.model_class = model_class
        
    @property
    def table_name(self):
        x = re.sub(r'(?<!^)(?=[A-Z])', '_', self.model_class.table_name).lower()
        return x

    def _get_fields(self):
        cursor = self._get_cursor()
        cursor.execute(
            f"SELECT * FROM {self.table_name} LIMIT 0"
        )
        return [Field(name=row[0], data_type=row[1]) for row in cursor.description]
    
    def filter_by(self, **kwargs):
        # Execute query
        # self.select('*', condition=Condition(**kwargs))
        return self.select('*', condition=Condition(**kwargs))
    
    def select(self, *field_names, chunk_size=2000, condition=None):
        # Build SELECT query
        if '*' in field_names:
            fields_format = '*'
            field_names = [field.name for field in self._get_fields()]
        else:
            fields_format = ', '.join(field_names)

        query = f"SELECT {fields_format} FROM {self.table_name}"
        vars = []
        if condition:
            query += f" WHERE {condition.sql_format}"
            vars += condition.query_vars

        # Execute query
        cursor = self._get_cursor()
        cursor.execute(query, vars)

        # Fetch data obtained with the previous query execution and transform it into `model_class` objects.
        # The fetching is done by batches to avoid to run out of memory.
        model_objects = list()
        is_fetching_completed = False
        while not is_fetching_completed:
            rows = cursor.fetchmany(size=chunk_size)
            for row in rows:
                row_data = dict(zip(field_names, row))
                x = Blank() # Create a blank object
                self.model_class.__bases__[0].__init__(x, new_record=False,**row_data) # Call the parent init on the blank object
                x.__class__ = self.model_class 
                # model_objects.append(self.model_class(new_record=False,**row_data))
                model_objects.append(x)
            is_fetching_completed = len(rows) < chunk_size

        return model_objects

    def bulk_insert(self, data):
        field_names = data[0].keys()
        values = list()
        for row in data:
            assert row.keys() == field_names
            values.append(tuple(row[field_name] for field_name in field_names))

        # Build INSERT query and vars following documentation at
        # https://www.psycopg.org/docs/usage.html#passing-parameters-to-sql-queries
        # values_format example with 3 rows to insert with 2 fields: << (?s, ?s), (?s, ?s), (?s, ?s) >>
        n_fields, n_rows = len(field_names), len(values)
        values_row_format = f'({", ".join(["?"]*n_fields)})'
        values_format = ", ".join([values_row_format]*n_rows)

        fields_format = ', '.join(field_names)
        query = f"INSERT INTO {self.table_name} ({fields_format}) VALUES {values_format}"
        vars = tuple(itertools.chain(*values))

        # Execute query
        self._execute_query(query, vars)

    def insert(self, **row_data):
        self.bulk_insert(data=[row_data])

    def update(self, new_data, condition=None):
        # Build UPDATE query
        new_data_format = ', '.join([f'{field_name} = {value}' for field_name, value in new_data.items()])
        query = f"UPDATE {self.table_name} SET {new_data_format}"
        vars = []
        if condition:
            query += f" WHERE {condition.sql_format}"
            vars += condition.query_vars

        # Execute query
        self._execute_query(query, vars)
        
    def updateOne(self,changedData, id):
        dataToChange = ''
        for key, value in changedData.items():
            dataToChange += f'{key} = \'{value}\','
        dataToChange = dataToChange[:-1]
        
        query = f"UPDATE {self.table_name} SET {dataToChange} WHERE id = {id}"
        self._execute_query(query, None)

    def delete(self, condition=None):
        # Build DELETE query
        query = f"DELETE FROM {self.table_name} "
        vars = []
        if condition:
            query += f" WHERE {condition.sql_format}"
            vars += condition.query_vars

        # Execute query
        self._execute_query(query, vars)
    
    def newRecord(self, data):
        columns = ''
        values = ''
        for key, value in data.items():
            columns += f'{key}, '
            values += f'\'{value}\', '
        columns = columns[:-2]
        values = values[:-2]
        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({values})"
        print(query)
        cursor = self._get_cursor()
        cursor.execute(query)
        id = cursor.lastrowid
        return id
        
        
        

def testfunc(string1:str):
    return exec()



def _wrapCustomInit(baseInit, self, data):
    result = baseInit(*self, **data)
    pk = self[0].__class__.primary_key
    self[0].__dict__[pk] = self[0].__class__.query.newRecord(data)
    return result

class MetaModel(type):
    manager_class = BaseManager
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
        self.session = BaseManager
        self.session.set_connection(None)
        self.__setFields()
        
    def __setFields(self):
        self.Field = Field
        self.ForeignKeyField = ForeignKeyField
        self.Relationship = Relationship
        self.NewRelationship = NewRelationship
        self.ForeignKey = ForeignKey
        
        
