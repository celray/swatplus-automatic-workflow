from peewee import *
from .base import OutputBase


class Plantwx(OutputBase):
	lai = DoubleField(null=True)
	bioms = DoubleField(null=True)
	yld = DoubleField(null=True)
	residue = DoubleField(null=True)
	sol_tmp = DoubleField(null=True)
	strsw = DoubleField(null=True)
	strsa = DoubleField(null=True)
	strstmp = DoubleField(null=True)
	strsn = DoubleField(null=True)
	strsp = DoubleField(null=True)
	nplt = DoubleField(null=True)
	percn = DoubleField(null=True)
	pplnt = DoubleField(null=True)
	tmx = DoubleField(null=True)
	tmn = DoubleField(null=True)
	tmpav = DoubleField(null=True)
	solarad = DoubleField(null=True)
	wndspd = DoubleField(null=True)
	rhum = DoubleField(null=True)
	phubas0 = DoubleField(null=True)
	lai_max = DoubleField(null=True)
	bm_max = DoubleField(null=True)
	bm_grow = DoubleField(null=True)
	c_gro = DoubleField(null=True)


class Basin_pw_day(Plantwx):
	pass


class Basin_pw_mon(Plantwx):
	pass


class Basin_pw_yr(Plantwx):
	pass


class Basin_pw_aa(Plantwx):
	pass


class Lsunit_pw_day(Plantwx):
	pass


class Lsunit_pw_mon(Plantwx):
	pass


class Lsunit_pw_yr(Plantwx):
	pass


class Lsunit_pw_aa(Plantwx):
	pass


class Hru_pw_day(Plantwx):
	pass


class Hru_pw_mon(Plantwx):
	pass


class Hru_pw_yr(Plantwx):
	pass


class Hru_pw_aa(Plantwx):
	pass


class Hru_lte_pw_day(Plantwx):
	pass


class Hru_lte_pw_mon(Plantwx):
	pass


class Hru_lte_pw_yr(Plantwx):
	pass


class Hru_lte_pw_aa(Plantwx):
	pass
