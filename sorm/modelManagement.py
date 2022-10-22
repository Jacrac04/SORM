from multiprocessing.dummy import Manager
from .dataBaseManagement.dataBaseMgr import BaseManager as NewBaseManager
from .fields.fields import Field, ForeignKey, NewRelationship, InstrumentedAttributeRelationship, InstrumentedAttribute, Relationship
import re

def _wrapCustomInit(baseInit, self, data):
    result = baseInit(*self, **data)
    pk = self[0].__class__.primary_key
    self[0].__dict__[pk] = self[0].__class__.query.newRecord(data)
    return result

class MetaModel(type):
    manager_class = NewBaseManager
    models = {}

        

    def __new__(cls, name, bases, attrs):
        inst:BaseModel = super().__new__(cls, name, bases, attrs)  # type: ignore
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
            # elif isinstance(attrs[attr], Relationship):
            #     y = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].parentcls)).lower()
            #     z = attrs[attr].back_populates
            #     print(attr, attrs[attr], attrs[attr].parentcls, attrs[attr].back_populates, re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].parentcls)).lower())
            #     x = property(fget=lambda self: MetaModel.models[y].query.filter_by(**{z:self.id}))
            elif isinstance(attrs[attr], NewRelationship):
                childcls = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].childcls)).lower()
                if attrs[attr].back_populates:
                    # print(attrs[attr])
                    string1 = re.sub(r'(?<!^)(?=[A-Z])', '_', (str(attrs[attr].childcls))).lower()+ ".id"
                    string2 = re.sub(r'(?<!^)(?=[A-Z])', '_', (inst.__name__)).lower()
                    # print(string1, string2)
                    def fget(self, string1=string1, string2=string2, childcls=childcls):
                        if string1 in MetaModel.models[string2].foreign_keys:
                            return MetaModel.models[childcls].query.filter_by(**{'id':getattr(self, self.foreign_keys[string1])})[0]
                        else:
                            return MetaModel.models[childcls].query.filter_by(**{MetaModel.models[childcls].foreign_keys[re.sub(r'(?<!^)(?=[A-Z])', '_', (str(self.__class__.__name__))).lower()+ ".id"]:self.id})
                    def fset(self, value, string1=string1, string2=string2, childcls=childcls):
                        # print(self, value, string1, string2, childcls)
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
    table_name:str
    manager:NewBaseManager
    foreign_keys:dict
    primary_key:str
    __name__:str 
    

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
        return cls._get_manager().get_fields()