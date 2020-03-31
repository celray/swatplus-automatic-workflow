from peewee import *
from . import base
from . import hru_parm_db


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
