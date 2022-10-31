from ..errors import PrimaryKeyError

class Field:
    """Field class for defining fields in a model.
    
    When a Model class containing an instance of a Felid is instantiated, the Felid is replaced with an InstrumentedAttribute.
    
    Attributes:
        - name: The name of the field.
        - data_type: The data type of the field. Not used currently. 
        - value: The value of the field.
        - primary_key: If the field is a primary key.
        
    Methods:
        - __repr__: Returns a string representation of the field. Dev use only.
        
    """
    def __init__(self, name:str, data_type:str, default_value=None, primary_key:bool=False) -> None:
        """__init__ method for the Field class.
        Args:
            - name: The name of the field.
            - data_type: The data type of the field. Not used currently. 
            - default_value: The default value of the field. Default is None.
            - primary_key: If the field is a primary key. Defaults to False.
            """
        self.name = name
        self.data_type = data_type
        self.value = default_value
        self.primary_key = primary_key
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.data_type})  -  {self.value}>"

    
class ForeignKey():
    """Foreign key class for defining foreign keys in a model.
    
    When a Model class containing an instance of a ForeignKey is instantiated, the ForeignKey is replaced with an InstrumentedAttribute.
    
    Attributes:
        - key: The foreign key. It is in the format of "table_name.field_name". 
        
    """
    def __init__(self, key) -> None:
        self.key = key 
    

class Relationship():
    """Relationship class for defining relationships in a model.
    
    When a Model class containing an instance of a Relationship is instantiated, the Relationship is replaced with an property defined in the MetaModel.
    
    Attributes:
        - related_cls_name: The name of the related class.
        - back_populates: The name of the attribute of the corresponding relationship. Not used currently.
    
    Methods:
        - __repr__: Returns a string representation of the relationship. Dev use only.
    """
    
    def __init__(self, related_cls_name:str, back_populates:str=None): # type: ignore
        self.related_cls_name = related_cls_name
        self.back_populates = back_populates
        # self.backref_field = parentcls.__dict__[back_populates]
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.related_cls_name} ({self.back_populates})>"   


class InstrumentedAttribute:
    """The InstrumentedAttribute class is used to replace the Field and ForeignKey class when a Model class is instantiated.
    
    Attributes:
        - name: The name of the field.
        - value: The value of the field.
        - is_primary_key: If the attribute represents a primary key.
        - is_foreign_key: If the attribute represents a foreign key.
        
    Methods:
        - __repr__: Returns a string representation of the field. Dev use only.
        - __get__: Returns the value of the attribute.
        - __set__: Sets the value of the attribute. If the attribute is a primary key, it raises a PrimaryKeyError.
    """
    
    def __init__(self, name:str, data_type:str, value=None, is_primary_key:bool=False, is_foreign_key:bool=False):
        """__init__ method for the InstrumentedAttribute class.
        
        Args:
            - name: The name of the field.
            - data_type: The data type of the field. Not used currently, in future it will be sued to ensure the data is the right type for the database felid
            - value: The value of the field.
            - is_primary_key: If the attribute represents a primary key. Defaults to False.
            - is_foreign_key: If the attribute represents a foreign key. Defaults to False.
        """
        self.name = name
        self.value = value
        self.is_primary_key = is_primary_key
        self.is_foreign_key = is_foreign_key
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.name} ({self.is_primary_key})  -  {self.value}>"
    
    def __get__(self, instance, owner):
        try:
            return instance.__dict__[self.name]
        except KeyError:
            print(f"KeyError: {self.name} not found in {instance.__dict__}")
            return None
    
    def __set__(self, instance, value):
        if self.is_primary_key:
            raise PrimaryKeyError()
        
        # Check to see if the instance has been initialized
        try:
            inited = instance.initialized 
        except AttributeError: 
            inited = False
        
        # Update the instance
        instance.__dict__[self.name] = value
        
        # If the instance has been initialized, update the database, else just update the instance
        if not inited:
            return instance        
        instance.__class__.query.updateOne({self.name: value}, id = instance.id) # Update the database
        return instance
