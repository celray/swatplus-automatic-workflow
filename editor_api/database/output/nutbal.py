from peewee import *
from .base import OutputBase, BaseModel


class Nutbal(OutputBase):
	grzn = DoubleField(null=True)
	grzp = DoubleField(null=True)
	lab_min_p = DoubleField(null=True)
	act_sta_p = DoubleField(null=True)
	fertn = DoubleField(null=True)
	fertp = DoubleField(null=True)
	fixn = DoubleField(null=True)
	denit = DoubleField(null=True)
	act_nit_n = DoubleField(null=True)
	act_sta_n = DoubleField(null=True)
	org_lab_p = DoubleField(null=True)
	rsd_nitorg_n = DoubleField(null=True)
	rsd_laborg_p = DoubleField(null=True)
	no3atmo = DoubleField(null=True)
	nh4atmo = DoubleField(null=True)
	nuptake = DoubleField(null=True)
	puptake = DoubleField(null=True)
	gwtrann = DoubleField(null=True)
	gwtranp = DoubleField(null=True)


class Basin_nb_day(Nutbal):
	pass


class Basin_nb_mon(Nutbal):
	pass


class Basin_nb_yr(Nutbal):
	pass


class Basin_nb_aa(Nutbal):
	pass


class Lsunit_nb_day(Nutbal):
	pass


class Lsunit_nb_mon(Nutbal):
	pass


class Lsunit_nb_yr(Nutbal):
	pass


class Lsunit_nb_aa(Nutbal):
	pass


class Hru_nb_day(Nutbal):
	pass


class Hru_nb_mon(Nutbal):
	pass


class Hru_nb_yr(Nutbal):
	pass


class Hru_nb_aa(Nutbal):
	pass
