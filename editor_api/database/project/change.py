from peewee import *
from . import base


class Cal_parms_cal(base.BaseModel):
	name = CharField()
	obj_typ = CharField()
	abs_min = DoubleField()
	abs_max = DoubleField()
	units = CharField(null=True)


class Calibration_cal(base.BaseModel):
	cal_parm = ForeignKeyField(Cal_parms_cal, on_delete='CASCADE', related_name='calibrations')
	chg_typ = CharField()  # absval, abschg, pctchg
	chg_val = DoubleField()
	soil_lyr1 = IntegerField(null=True)
	soil_lyr2 = IntegerField(null=True)
	yr1 = IntegerField(null=True)
	yr2 = IntegerField(null=True)
	day1 = IntegerField(null=True)
	day2 = IntegerField(null=True)


class Calibration_cal_cond(base.BaseModel):
	calibration_cal = ForeignKeyField(Calibration_cal, on_delete='CASCADE', related_name='conditions')
	cond_typ = CharField()  # hsg, texture, landuse, region
	cond_op = CharField() # = > <
	cond_val = DoubleField(null=True)
	cond_val_text = CharField(null=True)


class Calibration_cal_elem(base.BaseModel):
	calibration_cal = ForeignKeyField(Calibration_cal, on_delete='CASCADE', related_name='elements')
	obj_typ = CharField()
	obj_id = IntegerField()


class Codes_sft(base.BaseModel):
	hyd_hru = BooleanField()
	hyd_hrulte = BooleanField()
	plnt = BooleanField()
	sed = BooleanField()
	nut = BooleanField()
	ch_sed = BooleanField()
	ch_nut = BooleanField()
	res = BooleanField()


class Wb_parms_sft(base.BaseModel):
	name = CharField(unique=True)
	chg_typ = CharField()  # absval, abschg, pctchg
	neg = DoubleField()
	pos = DoubleField()
	lo = DoubleField()
	up = DoubleField()


class Water_balance_sft(base.BaseModel):
	name = CharField(unique=True)


class Water_balance_sft_item(base.BaseModel):
	water_balance_sft = ForeignKeyField(Water_balance_sft, on_delete='CASCADE', related_name='items')
	name = CharField()
	surq_rto = DoubleField()
	latq_rto = DoubleField()
	perc_rto = DoubleField()
	et_rto = DoubleField()
	tileq_rto = DoubleField()
	pet = DoubleField()
	sed = DoubleField()
	wyr = DoubleField()
	bfr = DoubleField()
	solp = DoubleField()


class Ch_sed_budget_sft(base.BaseModel):
	name = CharField(unique=True)

class Ch_sed_budget_sft_item(base.BaseModel):
	ch_sed_budget_sft = ForeignKeyField(Ch_sed_budget_sft, on_delete='CASCADE', related_name='items')
	name = CharField()
	cha_wide = DoubleField()
	cha_dc_accr = DoubleField()
	head_cut = DoubleField()
	fp_accr = DoubleField()


class Ch_sed_parms_sft(base.BaseModel):
	name = CharField(unique=True)
	chg_typ = CharField()  # absval, abschg, pctchg
	neg = DoubleField()
	pos = DoubleField()
	lo = DoubleField()
	up = DoubleField()


class Plant_parms_sft(base.BaseModel):
	name = CharField(unique=True)


class Plant_parms_sft_item(base.BaseModel):
	plant_parms_sft = ForeignKeyField(Plant_parms_sft, on_delete='CASCADE', related_name='items')
	var = CharField()
	name = CharField()
	init = DoubleField()
	chg_typ = CharField()  # absval, abschg, pctchg
	neg = DoubleField()
	pos = DoubleField()
	lo = DoubleField()
	up = DoubleField()


class Plant_gro_sft(base.BaseModel):
	name = CharField(unique=True)


class Plant_gro_sft_item(base.BaseModel):
	plant_gro_sft = ForeignKeyField(Plant_gro_sft, on_delete='CASCADE', related_name='items')
	name = CharField()
	yld = DoubleField()
	npp = DoubleField()
	lai_mx = DoubleField()
	wstress = DoubleField()
	astress = DoubleField()
	tstress = DoubleField()
