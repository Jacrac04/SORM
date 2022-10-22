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
        cursor = self._get_cursor()
        cursor.execute(query)
        id = cursor.lastrowid
        return id
        