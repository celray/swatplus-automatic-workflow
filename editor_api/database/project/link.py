from peewee import *
from . import base


class Chan_surf_lin(base.BaseModel):
	name = CharField(unique=True)


class Chan_surf_lin_ob(base.BaseModel):
	chan_surf_lin = ForeignKeyField(Chan_surf_lin, on_delete='CASCADE')
	obj_typ = IntegerField()
	obj_id = IntegerField()


class Chan_aqu_lin(base.BaseModel):
	name = CharField(unique=True)


class Chan_aqu_lin_ob(base.BaseModel):
	chan_aqu_lin = ForeignKeyField(Chan_aqu_lin, on_delete='CASCADE')
	aqu_no = IntegerField()
