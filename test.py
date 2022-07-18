
from dataclasses import fields
import re
import sqlite3


import itertools

import sqlite3

from utils import Field, BackrefField, ForeignKeyField, Relationship, InstrumentedAttribute, F, Condition


class BaseManager:
    connection = None

    @classmethod
    def set_connection(cls, database_settings):
        connection = sqlite3.connect("test.db", isolation_level=None)
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
        return self.model_class.table_name

    def _get_fields(self):
        cursor = self._get_cursor()
        cursor.execute(
            f"SELECT * FROM {self.table_name} LIMIT 0"
        )
        return [Field(name=row[0], data_type=row[1]) for row in cursor.description]
    
    def query(self, **kwargs):
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
                model_objects.append(self.model_class(**row_data))
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


class MetaModel(type):
    manager_class = BaseManager

    def __new__(cls, name, bases, attrs):
        inst = super().__new__(cls, name, bases, attrs)
        inst.manager = cls._get_manager(cls)
        inst.table_name = name.lower()
        for attr in attrs:
            if attr.startswith('_') or not (isinstance(attrs[attr], Field)):
                continue
            # print(attr)
            x = InstrumentedAttribute(attrs[attr].name, attrs[attr].data_type)
            setattr(inst, attr, x)
            pass
        return inst
    
    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()



class BaseModel(metaclass=MetaModel):
    table_name = ""

    def __init__(self, **row_data):
        # print(row_data)
        # for type(self).
        self.initialized = False
        for field_name, value in row_data.items():
            # setattr(self, field_name, getattr(self, field_name))
            setattr(self, field_name, value)
            
            # print(getattr(self, field_name))
            # setattr(self, field_name, value)
        self.initialized = True

        

    def __repr__(self):
        attrs_format = ", ".join([f'{field}={value}' for field, value in self.__dict__.items()])
        return f"<{self.__class__.__name__}: ({attrs_format})>"

    @classmethod
    def get_fields(cls):
        return cls._get_manager()._get_fields()



    
# ----------------------- Setup ----------------------- #
DB_SETTINGS = {
    'host': '127.0.0.1',
    'port': '5432',
    'database': 'ormify',
    'user': 'yank',
    'password': 'yank'
}

BaseManager.database_settings = DB_SETTINGS

BaseManager.set_connection(database_settings={
    'host': '127.0.0.1',
    'port': '5432',
    'database': 'pgtest',
    'user': 'yannick',
    'password': 'yannick'
})
# ----------------------- Usage ----------------------- #

    
class Referance(BaseModel):
    id = Field('id', data_type='int')
    empref = Field('empref', data_type='int')
    # children = Relationship('Referance', 'children', backref='Employee')
    
class Employee(BaseModel):
    id = Field('id', data_type='int')
    first_name = Field('first_name', data_type='varchar')
    last_name = Field('last_name', data_type='varchar')
    salary = Field('salary', data_type='int')
    ref = ForeignKeyField('ref', data_type='int', back_populates=Referance)


# print(Employee.get_fields())

employees_data = [
    {"first_name": "Yannick", "last_name": "KIKI", "salary": 1320000},
    {"first_name": "Corentin", "last_name": "ALLOH", "salary": 1320000}
]
# Employee.objects.bulk_insert(data=employees_data)

# SQL: INSERT INTO employees (first_name, last_name, salary)
#          VALUES ('Pythonista', 'BENINOSA', 2560000)
# ;
# Employee.objects.insert(first_name="Pythonista", last_name="BENINOSA", salary=2560000)

# SQL: SELECT salary, grade FROM employees;
# employees = Employee.objects.select('*', condition=Condition(first_name="Pythonista"))  # employees: List[Employee]
employees = Employee.objects.query(ref="1")
print(employees)
print(employees[0].first_name, employees[1].first_name  , employees[0].salary, employees[0].ref)
employees[0].first_name = "Yannick"
pass





# SQL: UPDATE employees SET salary = 3560000, age = 20 WHERE id > 4;
# Employee.objects.update(
#     new_data={'salary': 3560000, 'age': 20},
#     condition=Condition(id__gt=4)
# )

