from .databaseManagement.dataBaseMgr import BaseManager as NewBaseManager
from .fields.fields import Field, ForeignKey, InstrumentedAttribute, Relationship
import re

def _wrapCustomInit(baseInit, self, data):
    """Wraps the __init__ method of a Model class to allow for custom, user defined __init__ methods.

    Args:
        - baseInit: The __init__ method of the Model class.
        - self: The instance of the Model class.
        - data: The data to be passed to the __init__ method.

    Returns:
        - The result of the __init__ method and extra bits (an object).
    """
    print("modelManagement._wrapCustomInit", baseInit, self, data)
    result = baseInit(*self, **data)
    pk = self[0].__class__.primary_key
    data = {}
    for attr in self[0].__class__.fields:
        if attr != pk:
            data[attr] = getattr(self[0], attr)
    self[0].__dict__[pk] = self[0].__class__.query.newRecord(data)
    return result

class MetaModel(type):
    """Metaclass for the Model class.
    
    This is used to convert the user defined model class into a class that provides an interface to the database. It allows the model class to create new records as well as query the database for existing records.
    
    Class Attributes:
        - manager_class: The class that will be used to manage the database. Every model will have an instance of it.
        - models: A dictionary of all the models that have been created. The key is the name of the model and the value is the model class.
    
    Methods:
        - __new__: This is called when a new model class is created. It will create a new instance of the manager class and add it to the class as an attribute. It will also add the attributes to the class that will be used to query the database.
        - _get_manager: Returns an instance of the manager class. It takes a Model class as an argument. 
    
    Properties:
        - query: Returns an instance of the manager class. It takes a Model class as an argument. This is equivalent to a class method on the Model class.
    """
    manager_class = NewBaseManager
    models = {}

        

    def __new__(cls, name, bases, attrs):
        inst:BaseModel = super().__new__(cls, name, bases, attrs)  # type: ignore
        inst.manager = cls.manager_class(inst)
        inst.foreign_keys = {}
        inst.fields = [] 
        name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
        inst.table_name = name
        for attr in attrs:
            x = None
            related_cls_name = None
            foreign_key = None
            if (attr.startswith('_') and not attr.startswith('__init_')) or (not attr.startswith('__init_') and (not (isinstance(attrs[attr], Field) or isinstance(attrs[attr], Relationship) or isinstance(attrs[attr], Relationship) or isinstance(attrs[attr], ForeignKey)))):
                continue
            elif isinstance(attrs[attr], Field):
                inst.fields.append(attr)
                if attrs[attr].primary_key:
                    inst.primary_key = attr
                x = InstrumentedAttribute(attrs[attr].name, attrs[attr].data_type, attrs[attr].primary_key)
            elif isinstance(attrs[attr], Relationship):
                related_cls_name = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].related_cls_name)).lower()
                if attrs[attr].back_populates:                    
                    foreign_key = re.sub(r'(?<!^)(?=[A-Z])', '_', (str(attrs[attr].related_cls_name))).lower()+ ".id"                    
                    def fget(self, foreign_key=foreign_key, inst_table_name=inst.table_name, related_cls_name=related_cls_name,bp=attrs[attr].back_populates):
                        if foreign_key in MetaModel.models[inst_table_name].foreign_keys:
                            # For Child to Parent relationship
                            id_ofRelated = getattr(self, self.foreign_keys[foreign_key]) # This gets the attribute called the result of looking foreign key in the foreign_keys dict  
                            return MetaModel.models[related_cls_name].query.filter_by(**{'id':id_ofRelated})[0]
                        else:
                            # For Parent to Children relationship
                            child_fk_name = MetaModel.models[related_cls_name].foreign_keys[re.sub(r'(?<!^)(?=[A-Z])', '_', (str(self.__class__.__name__))).lower()+ ".id"]
                            return MetaModel.models[related_cls_name].query.filter_by(**{child_fk_name:self.id})
                    def fset(self, value, foreign_key=foreign_key, inst_table_name=inst.table_name, related_cls_name=related_cls_name):
                        if foreign_key in MetaModel.models[inst_table_name].foreign_keys:
                            # For Child to Parent relationship
                            attr_name = self.foreign_keys[foreign_key]
                            attr_obj = getattr(self, attr_name)
                            if not related_cls_name == value.__class__.__name__.lower():
                                raise ValueError(f"Can't set {related_cls_name} to a {value.__class__.__name__.lower()}")
                            setattr(self, attr_name, value.id)                                                  
                            
                    x = property(fget=fget, fset=fset)
                else: 
                    x = property(fget=lambda self, related_cls_name=related_cls_name: MetaModel.models[related_cls_name].query.filter_by(**{MetaModel.models[related_cls_name].foreign_keys[str(self.__class__.__name__).lower()+ ".id"]:self.id}))
            elif isinstance(attrs[attr], ForeignKey):
                inst.fields.append(attr)
                x = InstrumentedAttribute(attr, 'int', is_foreign_key=True) # TODO: Change so when the foreign key is updated it will update the relationship
                inst.foreign_keys[attrs[attr].key] = attr
                    
                    
            elif attr == '__init__':
                if name != 'base_model':
                    print('yeet', name, attr, attrs[attr])
                    x = lambda *args, attr=attr, **kwargs: _wrapCustomInit(attrs[attr], args, kwargs)
                else:
                    continue
            setattr(inst, attr, x)
            pass
        MetaModel.models[name] = inst
        return inst
    

    # This is equivalent to a class method on the Model class
    @property
    def query(model_cls):
        return model_cls.manager # type: ignore



class BaseModel(metaclass=MetaModel):
    """This is the base model that al user defined models will inherit from
    
    Class Attributes:
        - table_name: The name of the table in the database
        - manager: The manager that will be used to provide the query interface
        - foreign_keys: A dictionary of the foreign keys in the model. This is used in the relationship property.
        - primary_key: The name of the primary key of the model
        - __name__: The name of the model
    
    Attributes:
        - new_record: A boolean that is True if the record is new and False if it is not. This is used to determine if the record should be inserted into teh database.
        - **kwargs: The keyword arguments that are passed into the model should be the attributes of the model.
    
    Class Methods:
        - get_felids: Returns a list of the fields of the model
        
    Methods:
        - __repr__: Returns a string representation of the model. Dev use only
    """
    table_name:str
    manager:NewBaseManager
    foreign_keys:dict
    primary_key:str
    fields:list
    __name__:str 
    

    def __init__(self, new_record=True, **data):
        """This is the __init__ for the model
        
        This is the default __init__ for the model if one hasn't been user defined.
        
        Args:
            - new_record: A boolean that is True if the record is new and False if it is not. This is used to determine if the record should be inserted into the database.
            - **kwargs: The keyword arguments that are passed into the model should be the attributes of the model.
        """
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
        return cls.manager.get_fields()