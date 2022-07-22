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




class Field:
    def __init__(self, name, data_type):
        self.name = name
        self.data_type = data_type
        self.value = None
    
    def setValue(self, value):
        print(f"Setting value {value} to field {self.name}")
        if self.data_type == 'int':
            return value
            print(f"Value {value} converted to int: {self}")
        else:
            self.value = value
            return self

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})  -  {self.value}>"

    
# Class for backreference Field
class BackrefField(Field):
    def __init__(self, name, data_type, back_populates):
        super().__init__(name, data_type)
        self.back_populates = back_populates
        self.backref_field = None

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})>"

    def set_backref_field(self, backref_field):
        self.backref_field = backref_field
        self.backref_field.back_populates = self.back_populates
        self.backref_field.backref_field = self
        return self.backref_field
    
class ForeignKeyField(Field):
    def __init__(self, name, data_type, back_populates):
        super().__init__(name, data_type)
        self.back_populates = back_populates
        self.backref_field = None

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})>"

    # def set_backref_field(self, backref_field):
    #     self.backref_field = backref_field
    #     self.backref_field.back_populates = self.back_populates
    #     self.backref_field.backref_field = self
    #     return self.backref_field
    
    def setValue(self, value):
        return self.back_populates.objects.query(id = value)[0]
    
    
class Relationship():
    def __init__(self, parentcls, back_populates):
        self.parentcls = parentcls
        self.back_populates = back_populates
        # self.backref_field = parentcls.__dict__[back_populates]
    
class InstrumentedAttributeRelationship():
    def __init__(self, parentcls, back_populates):
        self.parentcls = parentcls
        self.back_populates = back_populates
        # self.backref_field = parentcls.__dict__[back_populates]
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        print(self, instance, owner)
        # print(exec(self.parentcls))
        return relationshipfunc
    def __set__(self, instance, value):
        pass
      
def relationshipfunc(parentcls):
    # return 
    return exec(parentcls)


class Blank():
    pass


class InstrumentedAttribute:
    def __init__(self, name, data_type):
        self.name = name
        # self.data_type = data_type
        self.value = None
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})  -  {self.value}>"
    
    def __get__(self, instance, owner):
        # print(instance, instance.__dict__)
        try:
            return instance.__dict__[self.name]
        except KeyError:
            print(f"KeyError: {self.name} not found in {instance.__dict__}")
            return None
    
    def __set__(self, instance, value):
        try:
            inited = instance.initialized
        except AttributeError:
            inited = False
        print(f"Setting value {value} to field {self.name}, {inited}")
        instance.__dict__[self.name] = value
        if not inited:
            return instance        
        instance.__class__.objects.updateOne({self.name: value}, id = instance.id)
        return instance