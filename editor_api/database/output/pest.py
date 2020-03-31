from peewee import *
from .base import OutputBase


class Hru_pest(OutputBase):
	pesticide = CharField(null=True)
	plant = DoubleField(null=True)
	soil = DoubleField(null=True)
	sed = DoubleField(null=True)
	surq = DoubleField(null=True)
	latq = DoubleField(null=True)
	tileq = DoubleField(null=True)
	perc = DoubleField(null=True)
	apply_s = DoubleField(null=True)
	apply_f = DoubleField(null=True)
	decay_s = DoubleField(null=True)
	decay_f = DoubleField(null=True)
	wash = DoubleField(null=True)


class Hru_pest_day(Hru_pest):
	pass


class Hru_pest_mon(Hru_pest):
	pass


class Hru_pest_yr(Hru_pest):
	pass


class Hru_pest_aa(Hru_pest):
	pass


class Basin_ls_pest_day(Hru_pest):
	pass


class Basin_ls_pest_mon(Hru_pest):
	pass


class Basin_ls_pest_yr(Hru_pest):
	pass


class Basin_ls_pest_aa(Hru_pest):
	pass


class Pest(OutputBase):
	pesticide = CharField(null=True)
	solpestin = DoubleField(null=True)
	solpestout = DoubleField(null=True)
	sorpestin = DoubleField(null=True)
	sorpestout = DoubleField(null=True)
	react_h2o = DoubleField(null=True)
	volat = DoubleField(null=True)
	settle = DoubleField(null=True)
	resuspend = DoubleField(null=True)
	diffuse = DoubleField(null=True)
	react_benth = DoubleField(null=True)
	bury_benth = DoubleField(null=True)
	water_stor = DoubleField(null=True)
	benthic = DoubleField(null=True)


class Basin_ch_pest_day(Pest):
	pass


class Basin_ch_pest_mon(Pest):
	pass


class Basin_ch_pest_yr(Pest):
	pass


class Basin_ch_pest_aa(Pest):
	pass


class Basin_res_pest_day(Pest):
	pass


class Basin_res_pest_mon(Pest):
	pass


class Basin_res_pest_yr(Pest):
	pass


class Basin_res_pest_aa(Pest):
	pass


class Channel_pest_day(Pest):
	pass


class Channel_pest_mon(Pest):
	pass


class Channel_pest_yr(Pest):
	pass


class Channel_pest_aa(Pest):
	pass


class Reservoir_pest_day(Pest):
	pass


class Reservoir_pest_mon(Pest):
	pass


class Reservoir_pest_yr(Pest):
	pass


class Reservoir_pest_aa(Pest):
	pass


class Aquifer_pest(OutputBase):
	pesticide = CharField(null=True)
	tot_in = DoubleField(null=True)
	sol_flo = DoubleField(null=True)
	sor_flo = DoubleField(null=True)
	sol_perc = DoubleField(null=True)
	react = DoubleField(null=True)
	stor_ave = DoubleField(null=True)
	stor_init = DoubleField(null=True)
	stor_final = DoubleField(null=True)


class Basin_aqu_pest_day(Aquifer_pest):
	pass


class Basin_aqu_pest_mon(Aquifer_pest):
	pass


class Basin_aqu_pest_yr(Aquifer_pest):
	pass


class Basin_aqu_pest_aa(Aquifer_pest):
	pass


class Aquifer_pest_day(Aquifer_pest):
	pass


class Aquifer_pest_mon(Aquifer_pest):
	pass


class Aquifer_pest_yr(Aquifer_pest):
	pass


class Aquifer_pest_aa(Aquifer_pest):
	pass
	