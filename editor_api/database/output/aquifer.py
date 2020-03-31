from peewee import *
from .base import OutputBase


class Aquifer(OutputBase):
	flo = DoubleField(null=True)
	stor = DoubleField(null=True)
	rchrg = DoubleField(null=True)
	seep = DoubleField(null=True)
	revap = DoubleField(null=True)
	dep_wt = DoubleField(null=True)
	no3_st = DoubleField(null=True)
	min = DoubleField(null=True)
	orgn = DoubleField(null=True)
	orgp = DoubleField(null=True)
	rchrgn = DoubleField(null=True)
	nloss = DoubleField(null=True)
	no3gw = DoubleField(null=True)
	seepno3 = DoubleField(null=True)
	flo_cha = DoubleField(null=True)
	flo_res = DoubleField(null=True)
	flo_ls = DoubleField(null=True)


class Basin_aqu_day(Aquifer):
	pass


class Basin_aqu_mon(Aquifer):
	pass


class Basin_aqu_yr(Aquifer):
	pass


class Basin_aqu_aa(Aquifer):
	pass


class Aquifer_day(Aquifer):
	pass


class Aquifer_mon(Aquifer):
	pass


class Aquifer_yr(Aquifer):
	pass


class Aquifer_aa(Aquifer):
	pass
