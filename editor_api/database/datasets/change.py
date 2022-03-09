from peewee import *
from . import base


class Cal_parms_cal(base.BaseModel):
	name = CharField()
	obj_typ = CharField()
	abs_min = DoubleField()
	abs_max = DoubleField()
	units = CharField(null=True)