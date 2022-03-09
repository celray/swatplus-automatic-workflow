from peewee import *
from . import base


class D_table_dtl(base.BaseModel):
	name = CharField(unique=True)
	file_name = CharField()
	description = CharField(null=True)


class D_table_dtl_cond(base.BaseModel):
	d_table = ForeignKeyField(D_table_dtl, on_delete='CASCADE', related_name='conditions')
	var = CharField()
	obj = CharField()
	obj_num = IntegerField()
	lim_var = CharField()
	lim_op = CharField()
	lim_const = DoubleField()
	description = CharField(null=True)


class D_table_dtl_cond_alt(base.BaseModel):
	cond = ForeignKeyField(D_table_dtl_cond, on_delete='CASCADE', related_name='alts')
	alt = CharField()


class D_table_dtl_act(base.BaseModel):
	d_table = ForeignKeyField(D_table_dtl, on_delete='CASCADE', related_name='actions')
	act_typ = CharField()
	obj = CharField()
	obj_num = IntegerField()
	name = CharField()
	option = CharField()
	const = DoubleField()
	const2 = DoubleField()
	fp = CharField()


class D_table_dtl_act_out(base.BaseModel):
	act = ForeignKeyField(D_table_dtl_act, on_delete='CASCADE', related_name='outcomes')
	outcome = BooleanField()
