from db import db
from models import User, PythonData, PythonDataAuthTokens, Project

x = User.query.filter_by(id=2)

data = PythonData.query.filter_by(id=6)[0]
# print(data.authTokens)
print(data.project)
print(data.project.owner)
data.project.owner = x[0]

print(data.project.owner)


authToken = PythonDataAuthTokens.query.filter_by(id=2)[0]

print(authToken.pythonData)



project = Project.query.filter_by(id=3)[0]

print(project.name)
print(project.owner)
print(project.pythonData)

pass

# def func(y):
#     return lambda x: x*y

# func2 = func(2)
# func3 = func(3)

# print(func2(3), func3(3))

# class thingMeta(type):
#     def __new__(cls, name, bases, dct):
#         # print(name, bases, dct)
#         i=0
#         for attr in dct:
#             if attr.startswith('__'):
#                 continue
#             print(i)
#             z=2
#             dct[attr] = lambda self, i=i: i*self.y
#             i +=1
#         return super().__new__(cls, name, bases, dct)

# class thing(metaclass=thingMeta):
#     x1 = 1
#     x2 = 2
#     x3 = 3
    
#     def __init__(self, y):
#         self.y = y

# thing1 = thing(2)
# thing2 = thing(3)

# print(thing1.x1(), thing1.x2(), thing1.x3())


# pass