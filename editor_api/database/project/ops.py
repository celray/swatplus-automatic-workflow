from peewee import *
from . import base
from . import hru_parm_db


class Graze_ops(base.BaseModel):
	name = CharField(unique=True)
	fert = ForeignKeyField(hru_parm_db.Fertilizer_frt, on_delete='CASCADE')
	bm_eat = DoubleField()
	bm_tramp = DoubleField()
	man_amt = DoubleField()
	grz_bm_min = DoubleField()
	description = TextField(null=True)


class Harv_ops(base.BaseModel):
	name = CharField(unique=True)
	harv_typ = CharField()  # grain, biomass, residue, tree, tuber
	harv_idx = DoubleField()
	harv_eff = DoubleField()
	harv_bm_min = DoubleField()
	description = TextField(null=True)


class Irr_ops(base.BaseModel):
	name = CharField(unique=True)
	amt_mm = DoubleField()
	eff_frac = DoubleField()
	sumq_frac = DoubleField()
	dep_sub = DoubleField()
	salt_ppm = DoubleField()
	no3_ppm = DoubleField()
	po4_ppm = DoubleField()
	description = TextField(null=True)


class Sweep_ops(base.BaseModel):
	name = CharField(unique=True)
	swp_eff = DoubleField()
	frac_curb = DoubleField()
	description = TextField(null=True)


class Fire_ops(base.BaseModel):
	name = CharField(unique=True)
	chg_cn2 = DoubleField()
	frac_burn = DoubleField()
	description = TextField(null=True)


class Chem_app_ops(base.BaseModel):
	name = CharField(unique=True)
	chem_form = CharField()  # solid, liquid
	app_typ = CharField()  # spread, spray, inject, direct
	app_eff = DoubleField()
	foliar_eff = DoubleField()
	inject_dp = DoubleField()
	surf_frac = DoubleField()
	drift_pot = DoubleField()
	aerial_unif = DoubleField()
	description = TextField(null=True)
