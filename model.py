class MetaModel(type):
    manager_class = BaseManager

    def __new__(cls, name, bases, attrs):
        inst = super().__new__(cls, name, bases, attrs)
        inst.manager = cls._get_manager(cls)
        inst.table_name = name.lower()
        for attr in attrs:
            if attr.startswith('_') or not (isinstance(attrs[attr], Field)):
                continue
            elif isinstance(attrs[attr], Field):
            # print(attr)
                x = InstrumentedAttribute(attrs[attr].name, attrs[attr].data_type)
            elif isinstance(attrs[attr], Relationship):
                x = InstrumentedAttributeRelationship(attrs[attr].name, attrs[attr].data_type, attrs[attr].backref_name)
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