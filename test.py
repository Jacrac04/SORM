from database import ORM
import uuid

db = ORM()

def uuidGen():
    return str(uuid.uuid4())

class Referance(db.Model):
    id = db.Field('id', data_type='int')
    empref = db.Field('empref', data_type='int')
    children = db.Relationship('Employee', 'ref')
    
class Employee(db.Model):
    id = db.Field('id', data_type='int')
    first_name = db.Field('first_name', data_type='varchar')
    last_name = db.Field('last_name', data_type='varchar')
    salary = db.Field('salary', data_type='int')
    ref = db.ForeignKeyField('ref', data_type='int', back_populates=Referance)
    
    def __init__(self, first_name, last_name, salary, ref=None):
        self.first_name = first_name
        self.salary = salary
        self.ref = ref
        self.last_name = uuidGen()
    


employees = Employee.query.filter_by(ref="1")
print(employees)
print(employees[0].first_name, employees[1].first_name  , employees[0].salary, employees[0].ref)
# employees[0].first_name = "Yannick"
referances = Referance.query.filter_by(id=1)
print(referances[0])
x = referances[0].children
print(x)

newEmp = Employee(first_name="Yannick", last_name="KIKI", salary=1320000)
print(newEmp.id, newEmp.first_name, newEmp.last_name, newEmp.salary, newEmp.ref)

pass

# class class1:
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age
#         print('Init 1')
    
    
# class class2(class1):
#     def __init__(self, name):
#         self.name = name
#         # super().__init__(name)
#         print('Init 2')
        
#     def bar(self):
#         print('bar')

# class Blank():
#     pass

# # Class2 Initiation With Normal Init
# x = class2('NameValue1')
# print(x.name)
# x.bar()

# # Class2 Initiation With Parent Init
# y = Blank() # Create a blank object
# class2.__bases__[0].__init__(y, 'NameValue2', 17) # Call the parent init on the blank object
# y.__class__ = class2 # Change the class of the blank object to class2
# print(y.name, y.age)
# y.bar()

 
pass