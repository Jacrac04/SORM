class Field:
    def __init__(self, name, data_type, primary_key=False):
        self.name = name
        self.data_type = data_type
        # print(f"Creating field {self.name} ({self.data_type})")
        self.value = None
        self.primary_key = primary_key
    
    def setValue(self, value):
        # print(f"Setting value {value} to field {self.name}")
        if self.data_type == 'int':
            return value
        else:
            self.value = value
            return self

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})  -  {self.value}>"

    
class ForeignKey():
    def __init__(self, key) -> None:
        self.key = key 
    

class Relationship():
    def __init__(self, related_cls_name, back_populates=None):
        self.related_cls_name = related_cls_name
        self.back_populates = back_populates
        # self.backref_field = parentcls.__dict__[back_populates]
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.related_cls_name} ({self.back_populates})>"   

class InstrumentedAttributeRelationship():
    def __init__(self, parentcls, back_populates):
        self.parentcls = parentcls
        self.back_populates = back_populates
        # self.backref_field = parentcls.__dict__[back_populates]
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return relationshipfunc
    def __set__(self, instance, value):
        pass
      
def relationshipfunc(parentcls):
    # return 
    return exec(parentcls)


class InstrumentedAttribute:
    def __init__(self, name, data_type, primary_key):
        self.name = name
        self.value = None
        self.primary_key = primary_key
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.primary_key})  -  {self.value}>"
    
    def __get__(self, instance, owner):
        try:
            return instance.__dict__[self.name]
        except KeyError:
            print(f"KeyError: {self.name} not found in {instance.__dict__}")
            return None
    
    def __set__(self, instance, value):
        if self.primary_key:
            raise Exception("Cannot set primary key")
        try:
            inited = instance.initialized
        except AttributeError:
            inited = False
        # print(f"Setting value {value} to field {self.name}, {inited}")
        instance.__dict__[self.name] = value
        if not inited:
            return instance        
        instance.__class__.query.updateOne({self.name: value}, id = instance.id)
        return instance
    
