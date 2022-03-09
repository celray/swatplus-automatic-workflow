from peewee import *
from . import base, decision_table, hru_parm_db, structural, init


class Management_sch(base.BaseModel):
	name = CharField(unique=True)


class Management_sch_auto(base.BaseModel):
	management_sch = ForeignKeyField(Management_sch, on_delete='CASCADE', related_name='auto_ops')
	d_table = ForeignKeyField(decision_table.D_table_dtl, on_delete='CASCADE')
	plant1 = CharField(null=True)
	plant2 = CharField(null=True)


class Management_sch_op(base.BaseModel):
	management_sch = ForeignKeyField(Management_sch, on_delete='CASCADE', related_name='operations')
	op_typ = CharField()
	mon = IntegerField()
	day = IntegerField()
	hu_sch = DoubleField()
	op_data1 = CharField(null=True)
	op_data2 = CharField(null=True)
	op_data3 = DoubleField()
	description = CharField(null=True)
	order = IntegerField()  # use this to order because using date is problematic due to skip 0 0


class Cntable_lum(base.BaseModel):
	name = CharField(unique=True)
	cn_a = DoubleField()
	cn_b = DoubleField()
	cn_c = DoubleField()
	cn_d = DoubleField()
	description = TextField(null=True)
	treat = CharField(null=True)
	cond_cov = CharField(null=True)


class Ovn_table_lum(base.BaseModel):
	name = CharField(unique=True)
	ovn_mean = DoubleField()
	ovn_min = DoubleField()
	ovn_max = DoubleField()
	description = TextField(null=True)


class Cons_prac_lum(base.BaseModel):
	name = CharField(unique=True)
	usle_p = DoubleField()
	slp_len_max = DoubleField()
	description = TextField(null=True)


class Landuse_lum(base.BaseModel):
	name = CharField(unique=True)
	cal_group = CharField(null=True)
	plnt_com = ForeignKeyField(init.Plant_ini, null=True, on_delete='SET NULL')
	mgt = ForeignKeyField(Management_sch, null=True, on_delete='SET NULL')
	cn2 = ForeignKeyField(Cntable_lum, null=True, on_delete='SET NULL')
	cons_prac = ForeignKeyField(Cons_prac_lum, null=True, on_delete='SET NULL')
	urban = ForeignKeyField(hru_parm_db.Urban_urb, null=True, on_delete='SET NULL')
	urb_ro = CharField(null=True)  # buildup_washoff or usgs_reg
	ov_mann = ForeignKeyField(Ovn_table_lum, null=True, on_delete='SET NULL')
	tile = ForeignKeyField(structural.Tiledrain_str, null=True, on_delete='SET NULL')
	sep = ForeignKeyField(structural.Septic_str, null=True, on_delete='SET NULL')
	vfs = ForeignKeyField(structural.Filterstrip_str, null=True, on_delete='SET NULL')
	grww = ForeignKeyField(structural.Grassedww_str, null=True, on_delete='SET NULL')
	bmp = ForeignKeyField(structural.Bmpuser_str, null=True, on_delete='SET NULL')
	description = TextField(null=True)
