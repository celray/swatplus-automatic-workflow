from peewee import *
from . import base


class Hydrology_hyd(base.BaseModel):
	name = CharField(unique=True)
	lat_ttime = DoubleField()
	lat_sed = DoubleField()
	can_max = DoubleField()
	esco = DoubleField()
	epco = DoubleField()
	orgn_enrich = DoubleField()
	orgp_enrich = DoubleField()
	evap_pothole = DoubleField()
	bio_mix = DoubleField()
	perco = DoubleField()
	lat_orgn = DoubleField()
	lat_orgp = DoubleField()
	harg_pet = DoubleField()
	cn_plntet = DoubleField()


class Topography_hyd(base.BaseModel):
	name = CharField(unique=True)
	slp = DoubleField()
	slp_len = DoubleField()
	lat_len = DoubleField()
	dist_cha = DoubleField()
	depos = DoubleField()
	type = CharField(null=True)  # sub or hru, for internal use; not in model - make this a drop-down in the editor!


class Field_fld(base.BaseModel):
	name = CharField(unique=True)
	len = DoubleField()
	wd = DoubleField()
	ang = DoubleField()
