from peewee import *
from . import base, init
from .decision_table import D_table_dtl


class Initial_res(base.BaseModel):
	name = CharField(unique=True)
	org_min = ForeignKeyField(init.Om_water_ini, on_delete='SET NULL', null=True)
	pest = ForeignKeyField(init.Pest_water_ini, on_delete='SET NULL', null=True)
	path = ForeignKeyField(init.Path_water_ini, on_delete='SET NULL', null=True)
	hmet = ForeignKeyField(init.Hmet_water_ini, on_delete='SET NULL', null=True)
	salt = ForeignKeyField(init.Salt_water_ini, on_delete='SET NULL', null=True)
	description = TextField(null=True)


class Hydrology_res(base.BaseModel):
	name = CharField(unique=True)
	yr_op = IntegerField()
	mon_op = IntegerField()
	area_ps = DoubleField()
	vol_ps = DoubleField()
	area_es = DoubleField()
	vol_es = DoubleField()
	k = DoubleField()
	evap_co = DoubleField()
	shp_co1 = DoubleField()
	shp_co2 = DoubleField()


class Nutrients_res(base.BaseModel):
	name = CharField(unique=True)
	mid_start = IntegerField()
	mid_end = IntegerField()
	mid_n_stl = DoubleField()
	n_stl = DoubleField()
	mid_p_stl = DoubleField()
	p_stl = DoubleField()
	chla_co = DoubleField()
	secchi_co = DoubleField()
	theta_n = DoubleField()
	theta_p = DoubleField()
	n_min_stl = DoubleField()
	p_min_stl = DoubleField()


class Sediment_res(base.BaseModel):
	name = CharField(unique=True)
	sed_amt = DoubleField()
	d50 = DoubleField()
	carbon = DoubleField()
	bd = DoubleField()
	sed_stl = DoubleField()
	stl_vel = DoubleField()


class Weir_res(base.BaseModel):
	name = CharField(unique=True)
	num_steps = DoubleField()
	disch_co = DoubleField()
	energy_co = DoubleField()
	weir_wd = DoubleField()
	vel_co = DoubleField()
	dp_co = DoubleField()


class Reservoir_res(base.BaseModel):
	name = CharField(unique=True)
	init = ForeignKeyField(Initial_res, null=True, on_delete='SET NULL')
	hyd = ForeignKeyField(Hydrology_res, null=True, on_delete='SET NULL')
	rel = ForeignKeyField(D_table_dtl, null=True, on_delete='SET NULL')
	sed = ForeignKeyField(Sediment_res, null=True, on_delete='SET NULL')
	nut = ForeignKeyField(Nutrients_res, null=True, on_delete='SET NULL')
	description = TextField(null=True)


class Hydrology_wet(base.BaseModel):
	name = CharField(unique=True)
	hru_ps = DoubleField()
	dp_ps = DoubleField()
	hru_es = DoubleField()
	dp_es = DoubleField()
	k = DoubleField()
	evap = DoubleField()
	vol_area_co = DoubleField()
	vol_dp_a = DoubleField()
	vol_dp_b = DoubleField()
	hru_frac = DoubleField()


class Wetland_wet(base.BaseModel):
	name = CharField(unique=True)
	init = ForeignKeyField(Initial_res, null=True, on_delete='SET NULL')
	hyd = ForeignKeyField(Hydrology_wet, null=True, on_delete='SET NULL')
	rel = ForeignKeyField(D_table_dtl, null=True, on_delete='SET NULL')
	sed = ForeignKeyField(Sediment_res, null=True, on_delete='SET NULL')
	nut = ForeignKeyField(Nutrients_res, null=True, on_delete='SET NULL')
	description = TextField(null=True)
