
from db import db



class Parent(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    children = db.NewRelationship('Child')


class Child(db.Model):
    id = db.Field('id', data_type='int', primary_key=True)
    parent_id = db.ForeignKey('parent.id')
    parent = db.NewRelationship('Parent', back_populates='children')

testChild = Child.query.filter_by(id=1)[0]

print(testChild.parent)


testParent = Parent.query.filter_by(id=1)[0]

print(testParent.children)


pass