from peewee import *
from . import base


class Septic_str(base.BaseModel):
	name = CharField(unique=True)
	typ = IntegerField()
	yr = IntegerField()
	operation = IntegerField()
	residents = DoubleField()
	area = DoubleField()
	t_fail = IntegerField()
	dp_bioz = DoubleField()
	thk_bioz = DoubleField()
	cha_dist = DoubleField()
	sep_dens = DoubleField()
	bm_dens = DoubleField()
	bod_decay = DoubleField()
	bod_conv = DoubleField()
	fc_lin = DoubleField()
	fc_exp = DoubleField()
	fecal_decay = DoubleField()
	tds_conv = DoubleField()
	mort = DoubleField()
	resp = DoubleField()
	slough1 = DoubleField()
	slough2 = DoubleField()
	nit = DoubleField()
	denit = DoubleField()
	p_sorp = DoubleField()
	p_sorp_max = DoubleField()
	solp_slp = DoubleField()
	solp_int = DoubleField()


class Bmpuser_str(base.BaseModel):
	name = CharField(unique=True)
	flag = IntegerField()
	sed_eff = DoubleField()
	ptlp_eff = DoubleField()
	solp_eff = DoubleField()
	ptln_eff = DoubleField()
	soln_eff = DoubleField()
	bact_eff = DoubleField()
	description = TextField(null=True)


class Filterstrip_str(base.BaseModel):
	name = CharField(unique=True)
	flag = IntegerField()
	fld_vfs = DoubleField()
	con_vfs = DoubleField()
	cha_q = DoubleField()
	description = TextField(null=True)


class Grassedww_str(base.BaseModel):
	name = CharField(unique=True)
	flag = IntegerField()
	mann = DoubleField()
	sed_co = DoubleField()
	dp = DoubleField()
	wd = DoubleField()
	len = DoubleField()
	slp = DoubleField()
	description = TextField(null=True)


class Tiledrain_str(base.BaseModel):
	name = CharField(unique=True)
	dp = DoubleField()
	t_fc = DoubleField()
	lag = DoubleField()
	rad = DoubleField()
	dist = DoubleField()
	drain = DoubleField()
	pump = DoubleField()
	lat_ksat = DoubleField()
