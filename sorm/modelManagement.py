from multiprocessing.dummy import Manager
from .dataBaseManagement.dataBaseMgr import BaseManager as NewBaseManager
from .fields.fields import Field, ForeignKey, InstrumentedAttributeRelationship, InstrumentedAttribute, Relationship
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
            related_cls_name = None
            foreign_key = None
            # string2 = None
            if (attr.startswith('_') and not attr.startswith('__init_')) or (not attr.startswith('__init_') and (not (isinstance(attrs[attr], Field) or isinstance(attrs[attr], Relationship) or isinstance(attrs[attr], Relationship) or isinstance(attrs[attr], ForeignKey)))):
                continue
            elif isinstance(attrs[attr], Field):
                if attrs[attr].primary_key:
                    inst.primary_key = attr
                x = InstrumentedAttribute(attrs[attr].name, attrs[attr].data_type, attrs[attr].primary_key)
            elif isinstance(attrs[attr], Relationship):
                related_cls_name = re.sub(r'(?<!^)(?=[A-Z])', '_', (attrs[attr].related_cls_name)).lower()
                if attrs[attr].back_populates:
                    
                    foreign_key = re.sub(r'(?<!^)(?=[A-Z])', '_', (str(attrs[attr].related_cls_name))).lower()+ ".id"
                    # string2 = re.sub(r'(?<!^)(?=[A-Z])', '_', (inst.__name__)).lower()
                    
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
                x = InstrumentedAttribute(attr, 'int', False) # TODO: Change so when the foreign key is updated it will update the relationship
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