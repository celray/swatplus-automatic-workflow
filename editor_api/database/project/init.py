from peewee import *
from . import base, hru_parm_db, soils


class Plant_ini(base.BaseModel):
	name = CharField(unique=True)
	rot_yr_ini = IntegerField()
	description = TextField(null=True)


class Plant_ini_item(base.BaseModel):
	plant_ini = ForeignKeyField(Plant_ini, on_delete='CASCADE', related_name="plants")
	plnt_name = ForeignKeyField(hru_parm_db.Plants_plt, on_delete='CASCADE', null=True)
	lc_status = BooleanField()
	lai_init = DoubleField()
	bm_init = DoubleField()
	phu_init = DoubleField()
	plnt_pop = DoubleField()
	yrs_init = DoubleField()
	rsd_init = DoubleField()


class Om_water_ini(base.BaseModel):
	name = CharField(unique=True)
	flo = DoubleField()
	sed = DoubleField()
	orgn = DoubleField()
	sedp = DoubleField()
	no3 = DoubleField()
	solp = DoubleField()
	chl_a = DoubleField()
	nh3 = DoubleField()
	no2 = DoubleField()
	cbn_bod = DoubleField()
	dis_ox = DoubleField()
	san = DoubleField()
	sil = DoubleField()
	cla = DoubleField()
	sag = DoubleField()
	lag = DoubleField()
	grv = DoubleField()
	tmp = DoubleField()
	c = DoubleField()

	@staticmethod
	def get_default_data():
		"""return [
			{
				'id': 1,
				'name': 'no_init',
				'flo': 0,
				'sed': 0,
				'orgn': 0,
				'sedp': 0,
				'no3': 0,
				'solp': 0,
				'chl_a': 0,
				'nh3': 0,
				'no2': 0,
				'cbn_bod': 0,
				'dis_ox': 0,
				'san': 0,
				'sil': 0,
				'cla': 0,
				'sag': 0,
				'lag': 0,
				'grv': 0,
				'tmp': 0,
				'c': 0
			},
			{
				'id': 2,
				'name': 'low_init',
				'flo': 0.8,
				'sed': 1000,
				'orgn': 90,
				'sedp': 80,
				'no3': 70,
				'solp': 60,
				'chl_a': 30,
				'nh3': 20,
				'no2': 10,
				'cbn_bod': 9,
				'dis_ox': 8,
				'san': 2,
				'sil': 1,
				'cla': 1000,
				'sag': 90,
				'lag': 80,
				'grv': 70,
				'tmp': 60,
				'c': 50
			},
			{
				'id': 3,
				'name': 'high_init',
				'flo': 0.9,
				'sed': 1100,
				'orgn': 99,
				'sedp': 88,
				'no3': 77,
				'solp': 66,
				'chl_a': 33,
				'nh3': 22,
				'no2': 11,
				'cbn_bod': 19,
				'dis_ox': 28,
				'san': 82,
				'sil': 91,
				'cla': 1900,
				'sag': 98,
				'lag': 87,
				'grv': 76,
				'tmp': 65,
				'c': 54
			}
		]"""
		return [{
				'id': 1,
				'name': 'no_init',
				'flo': 0,
				'sed': 0,
				'orgn': 0,
				'sedp': 0,
				'no3': 0,
				'solp': 0,
				'chl_a': 0,
				'nh3': 0,
				'no2': 0,
				'cbn_bod': 0,
				'dis_ox': 0,
				'san': 0,
				'sil': 0,
				'cla': 0,
				'sag': 0,
				'lag': 0,
				'grv': 0,
				'tmp': 0,
				'c': 0
			}]


class Pest_hru_ini(base.BaseModel):
	name = CharField(unique=True)


class Pest_hru_ini_item(base.BaseModel):
	pest_hru_ini = ForeignKeyField(Pest_hru_ini, on_delete='CASCADE', related_name="pest_hrus")
	name = ForeignKeyField(hru_parm_db.Pesticide_pst, on_delete='CASCADE', null=True)
	plant = DoubleField()
	soil = DoubleField()


class Pest_water_ini(base.BaseModel):
	name = CharField(unique=True)


class Pest_water_ini_item(base.BaseModel):
	pest_water_ini = ForeignKeyField(Pest_water_ini, on_delete='CASCADE', related_name="pest_waters")
	name = ForeignKeyField(hru_parm_db.Pesticide_pst, on_delete='CASCADE', null=True)
	water_sol = DoubleField()
	water_sor = DoubleField()
	benthic_sol = DoubleField()
	benthic_sor = DoubleField()


class Path_hru_ini(base.BaseModel):
	name = CharField(unique=True)


class Path_hru_ini_item(base.BaseModel):
	path_hru_ini = ForeignKeyField(Path_hru_ini, on_delete='CASCADE', related_name="path_hrus")
	name = ForeignKeyField(hru_parm_db.Pathogens_pth, on_delete='CASCADE', null=True)
	plant = DoubleField()
	soil = DoubleField()


class Path_water_ini(base.BaseModel):
	name = CharField(unique=True)


class Path_water_ini_item(base.BaseModel):
	path_water_ini = ForeignKeyField(Path_water_ini, on_delete='CASCADE', related_name="path_waters")
	name = ForeignKeyField(hru_parm_db.Pathogens_pth, on_delete='CASCADE', null=True)
	water_sol = DoubleField()
	water_sor = DoubleField()
	benthic_sol = DoubleField()
	benthic_sor = DoubleField()


class Hmet_hru_ini(base.BaseModel):
	name = CharField(unique=True)


class Hmet_water_ini(base.BaseModel):
	name = CharField(unique=True)


class Salt_hru_ini(base.BaseModel):
	name = CharField(unique=True)


class Salt_water_ini(base.BaseModel):
	name = CharField(unique=True)


class Soil_plant_ini(base.BaseModel):
	name = CharField(unique=True)
	sw_frac = DoubleField()
	nutrients = ForeignKeyField(soils.Nutrients_sol, on_delete='SET NULL', null=True)
	pest = ForeignKeyField(Pest_hru_ini, on_delete='SET NULL', null=True)
	path = ForeignKeyField(Path_hru_ini, on_delete='SET NULL', null=True)
	hmet = ForeignKeyField(Hmet_hru_ini, on_delete='SET NULL', null=True)
	salt = ForeignKeyField(Salt_hru_ini, on_delete='SET NULL', null=True)
