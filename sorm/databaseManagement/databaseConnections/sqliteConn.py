from .templateConnection import DataBaseConnection
import sqlite3

class SQLITEBaseConnection(DataBaseConnection):
    @classmethod
    def set_connection(cls, connectionSettings: dict) -> None:    
        cls._connectionSettings = connectionSettings
        cls._shouldCommit = True if 'commit' not in connectionSettings else connectionSettings['commit']
        cls._connection = sqlite3.connect(connectionSettings['databaseURI'], isolation_level=connectionSettings['isolation_level'], check_same_thread=False) # check_same_thread=False is a temp fix for SQLite objects created in a thread can only be used in that same thread
        cls._cursor = cls._connection.cursor()
        cls._cursor.execute("PRAGMA foreign_keys = ON")
        cls._connection.commit()
    
    @classmethod
    def _get_cursor(cls):
        return cls._cursor

    @classmethod
    def _commit(cls):
        if cls._shouldCommit:
            cls._connection.commit()
    
    @classmethod
    def get_fields(cls, table_name):
        cls._cursor.execute(f"PRAGMA table_info({table_name})")
        return [row[1] for row in cls._cursor.fetchall()]
    
    @classmethod
    def select(cls, table_name, *field_names, chunk_size=2000, condition=None):
        if not field_names:
            field_names = '*' # cls.get_fields(table_name)
        if condition:
            cls._cursor.execute(f"SELECT {', '.join(field_names)} FROM {table_name} WHERE {condition.sql_format}", condition.query_vars)  # type: ignore
        else:
            cls._cursor.execute(f"SELECT {', '.join(field_names)} FROM {table_name}")  # type: ignore
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
        cls._commit()
        
    @classmethod
    def update(cls, table_name, dataToChange: dict, condition) -> None:
        query = f"UPDATE {table_name} SET {', '.join([f'{field} = ?' for field in dataToChange.keys()])} WHERE {condition.sql_format}"
        cls._cursor.execute(query, tuple(dataToChange.values()) + tuple(condition.query_vars))
        cls._commit()
    
    @classmethod
    def get_last_row_id(cls):
        return cls._cursor.lastrowid