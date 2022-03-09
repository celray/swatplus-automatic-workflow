from peewee import *
from .base import OutputBase


class Losses(OutputBase):
	sedyld = DoubleField(null=True)
	sedorgn = DoubleField(null=True)
	sedorgp = DoubleField(null=True)
	surqno3 = DoubleField(null=True)
	lat3no3 = DoubleField(null=True)
	surqsolp = DoubleField(null=True)
	usle = DoubleField(null=True)
	sedmin = DoubleField(null=True)
	tileno3 = DoubleField(null=True)
	lchlabp = DoubleField(null=True)
	tilelabp = DoubleField(null=True)
	satexn = DoubleField(null=True)


class Basin_ls_day(Losses):
	pass


class Basin_ls_mon(Losses):
	pass


class Basin_ls_yr(Losses):
	pass


class Basin_ls_aa(Losses):
	pass


class Lsunit_ls_day(Losses):
	pass


class Lsunit_ls_mon(Losses):
	pass


class Lsunit_ls_yr(Losses):
	pass


class Lsunit_ls_aa(Losses):
	pass


class Hru_ls_day(Losses):
	pass


class Hru_ls_mon(Losses):
	pass


class Hru_ls_yr(Losses):
	pass


class Hru_ls_aa(Losses):
	pass


class Hru_lte_ls_day(Losses):
	pass


class Hru_lte_ls_mon(Losses):
	pass


class Hru_lte_ls_yr(Losses):
	pass


class Hru_lte_ls_aa(Losses):
	pass
