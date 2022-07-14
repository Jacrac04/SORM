
from dataclasses import fields
import re
import sqlite3


import itertools

import sqlite3

from utils import Field


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
        cursor.execute(query, vars)

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
        # Get fields to insert [fx, fy, fz] and set values in this format [(x1, y1, z1), (x2, y2, z2), ... ] to
        # facilitate the INSERT query building
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
        print(attrs)
        return inst
    
    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    table_name = ""

    def __init__(self, **row_data):
        print(row_data)
        # for type(self).
        for field_name, value in row_data.items():
            setattr(self, field_name, getattr(self, field_name).setValue(value))
            print(getattr(self, field_name))
            # setattr(self, field_name, value)

    def __repr__(self):
        attrs_format = ", ".join([f'{field}={value}' for field, value in self.__dict__.items()])
        return f"<{self.__class__.__name__}: ({attrs_format})>"

    @classmethod
    def get_fields(cls):
        return cls._get_manager()._get_fields()

class F:
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'

    def __init__(self, field_name=None):
        self.sql_format = field_name
        
    def __add__(self, other):
        return self._combine(other, operator=self.ADD)

    def __radd__(self, other):
        return self._combine(other, operator=self.ADD, is_reversed=True)

    def __sub__(self, other):
        return self._combine(other, operator=self.SUB)

    def __rsub__(self, other):
        return self._combine(other, operator=self.SUB, is_reversed=True)

    def __mul__(self, other):
        return self._combine(other, operator=self.MUL)

    def __rmul__(self, other):
        return self._combine(other, operator=self.MUL, is_reversed=True)

    def __truediv__(self, other):
        return self._combine(other, operator=self.DIV)

    def __rtruediv__(self, other):
        return self._combine(other, operator=self.DIV, is_reversed=True)

    def _combine(self, other, operator, is_reversed=False):
        f_obj = F()
        part_left = self.sql_format
        part_right = other.sql_format if isinstance(other, F) else other
        if is_reversed:
            part_left, part_right = part_right, part_left
        f_obj.sql_format = f'{part_left} {operator} {part_right}'
        return f_obj

class Condition:
    operations_map = {
        'eq': '=',
        'lt': '<',
        'lte': '<=',
        'gt': '>',
        'gte': '>=',
        'in': 'IN'
    }

    def __init__(self, **kwargs):
        sql_format_parts = list()
        self.query_vars = list()
        for expr, value in kwargs.items():
            if '__' not in expr:
                expr += '__eq'
            field, operation_expr = expr.split('__')
            operation_str = self.operations_map[operation_expr]

            if isinstance(value, F):
                f_obj = value
                sql_format_parts.append(f'{field} {operation_str} {f_obj.sql_format}')
            elif isinstance(value, list):
                vars_list = value
                sql_format_parts.append(f'{field} {operation_str} ({", ".join(["?"]*len(vars_list))})')
                self.query_vars += vars_list
            else:
                sql_format_parts.append(f'{field} {operation_str} ?')
                self.query_vars.append(value)
        self.sql_format = ' AND '.join(sql_format_parts)

    def __or__(self, other):
        return self._merge_with(other, logical_operator='OR')

    def __and__(self, other):
        return self._merge_with(other, logical_operator='AND')

    def _merge_with(self, other, logical_operator='AND'):
        condition_resulting = Condition()
        condition_resulting.sql_format = f"({self.sql_format}) {logical_operator} ({other.sql_format})"
        condition_resulting.query_vars = self.query_vars + other.query_vars
        return condition_resulting


    
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
class Employee(BaseModel):
    id = Field('id', data_type='int')
    first_name = Field('first_name', data_type='varchar')
    last_name = Field('last_name', data_type='varchar')
    salary = Field('salary', data_type='int')
    
    
class ReferanceTable(BaseModel):
    table_name = "referance_table"
    manager_class = BaseManager 


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
employees = Employee.objects.query(first_name="Pythonista")
print(employees[0].first_name, employees[0].id  , employees[0].salary)
pass





# SQL: UPDATE employees SET salary = 3560000, age = 20 WHERE id > 4;
# Employee.objects.update(
#     new_data={'salary': 3560000, 'age': 20},
#     condition=Condition(id__gt=4)
# )

