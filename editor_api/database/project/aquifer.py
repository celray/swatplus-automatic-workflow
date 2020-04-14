from peewee import *
from . import base, init


class Initial_aqu(base.BaseModel):
	name = CharField(unique=True)
	org_min = ForeignKeyField(init.Om_water_ini, on_delete='SET NULL', null=True)
	pest = ForeignKeyField(init.Pest_water_ini, on_delete='SET NULL', null=True)
	path = ForeignKeyField(init.Path_water_ini, on_delete='SET NULL', null=True)
	hmet = ForeignKeyField(init.Hmet_water_ini, on_delete='SET NULL', null=True)
	salt = ForeignKeyField(init.Salt_water_ini, on_delete='SET NULL', null=True)
	description = TextField(null=True)


class Aquifer_aqu(base.BaseModel):
	name = CharField(unique=True)
	init = ForeignKeyField(Initial_aqu, null=True, on_delete='SET NULL')
	gw_flo = DoubleField()
	dep_bot = DoubleField()
	dep_wt = DoubleField()
	no3_n = DoubleField()
	sol_p = DoubleField()
	ptl_n = DoubleField()
	ptl_p = DoubleField()
	bf_max = DoubleField()
	alpha_bf = DoubleField()
	revap = DoubleField()
	rchg_dp = DoubleField()
	spec_yld = DoubleField()
	hl_no3n = DoubleField()
	flo_min = DoubleField()
	revap_min = DoubleField()

	@staticmethod
	def get_default_shallow(aquid, name, init_id):
		return {
			'id': aquid,
			'name': name,
			'init': init_id,
			'gw_flo': 0.05,
			'dep_bot': 10,
			'dep_wt': 3,
			'no3_n': 0,
			'sol_p': 0,
			'ptl_n': 0,
			'ptl_p': 0,
			'bf_max': 1,
			'alpha_bf': 0.05,
			'revap': 0.02,
			'rchg_dp': 0.05,
			'spec_yld': 0.05,
			'hl_no3n': 0,
			'flo_min': 3,
			'revap_min': 5
		}

	@staticmethod
	def get_default_deep(aquid, name, init_id):
		return {
			'id': aquid,
			'name': name,
			'init': init_id,
			'gw_flo': 0,
			'dep_bot': 100,
			'dep_wt': 20,
			'no3_n': 0,
			'sol_p': 0,
			'ptl_n': 0,
			'ptl_p': 0,
			'bf_max': 1,
			'alpha_bf': 0.01,
			'revap': 0,
			'rchg_dp': 0,
			'spec_yld': 0.03,
			'hl_no3n': 0,
			'flo_min': 0,
			'revap_min': 0
		}
