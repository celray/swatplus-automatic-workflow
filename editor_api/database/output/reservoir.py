from peewee import *
from .base import OutputBase, BaseModel


class Reservoir(OutputBase):
	area = DoubleField(null=True)
	precip = DoubleField(null=True)
	evap = DoubleField(null=True)
	seep = DoubleField(null=True)
	flo_stor = DoubleField(null=True)
	sed_stor = DoubleField(null=True)
	orgn_stor = DoubleField(null=True)
	sedp_stor = DoubleField(null=True)
	no3_stor = DoubleField(null=True)
	solp_stor = DoubleField(null=True)
	chla_stor = DoubleField(null=True)
	nh3_stor = DoubleField(null=True)
	no2_stor = DoubleField(null=True)
	cbod_stor = DoubleField(null=True)
	dox_stor = DoubleField(null=True)
	san_stor = DoubleField(null=True)
	sil_stor = DoubleField(null=True)
	cla_stor = DoubleField(null=True)
	sag_stor = DoubleField(null=True)
	lag_stor = DoubleField(null=True)
	grv_stor = DoubleField(null=True)
	temp_stor = DoubleField(null=True)
	flo_in = DoubleField(null=True)
	sed_in = DoubleField(null=True)
	orgn_in = DoubleField(null=True)
	sedp_in = DoubleField(null=True)
	no3_in = DoubleField(null=True)
	solp_in = DoubleField(null=True)
	chla_in = DoubleField(null=True)
	nh3_in = DoubleField(null=True)
	no2_in = DoubleField(null=True)
	cbod_in = DoubleField(null=True)
	dox_in = DoubleField(null=True)
	san_in = DoubleField(null=True)
	sil_in = DoubleField(null=True)
	cla_in = DoubleField(null=True)
	sag_in = DoubleField(null=True)
	lag_in = DoubleField(null=True)
	grv_in = DoubleField(null=True)
	temp_in = DoubleField(null=True)
	flo_out = DoubleField(null=True)
	sed_out = DoubleField(null=True)
	orgn_out = DoubleField(null=True)
	sedp_out = DoubleField(null=True)
	no3_out = DoubleField(null=True)
	solp_out = DoubleField(null=True)
	chla_out = DoubleField(null=True)
	nh3_out = DoubleField(null=True)
	no2_out = DoubleField(null=True)
	cbod_out = DoubleField(null=True)
	dox_out = DoubleField(null=True)
	san_out = DoubleField(null=True)
	sil_out = DoubleField(null=True)
	cla_out = DoubleField(null=True)
	sag_out = DoubleField(null=True)
	lag_out = DoubleField(null=True)
	grv_out = DoubleField(null=True)
	temp_out = DoubleField(null=True)


class Basin_res_day(Reservoir):
	pass


class Basin_res_mon(Reservoir):
	pass


class Basin_res_yr(Reservoir):
	pass


class Basin_res_aa(Reservoir):
	pass


class Reservoir_day(Reservoir):
	pass


class Reservoir_mon(Reservoir):
	pass


class Reservoir_yr(Reservoir):
	pass


class Reservoir_aa(Reservoir):
	pass


class Wetland_day(Reservoir):
	pass


class Wetland_mon(Reservoir):
	pass


class Wetland_yr(Reservoir):
	pass


class Wetland_aa(Reservoir):
	pass
