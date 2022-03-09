from peewee import *
from .base import OutputBase


class Waterbal(OutputBase):
	precip = DoubleField(null=True)
	snofall = DoubleField(null=True)
	snomlt = DoubleField(null=True)
	surq_gen = DoubleField(null=True)
	latq = DoubleField(null=True)
	wateryld = DoubleField(null=True)
	perc = DoubleField(null=True)
	et = DoubleField(null=True)
	tloss = DoubleField(null=True)
	eplant = DoubleField(null=True)
	esoil = DoubleField(null=True)
	surq_cont = DoubleField(null=True)
	cn = DoubleField(null=True)
	sw_init = DoubleField(null=True)
	sw_final = DoubleField(null=True)
	sw_ave = DoubleField(null=True)
	sw_300 = DoubleField(null=True)
	sno_init = DoubleField(null=True)
	sno_final = DoubleField(null=True)
	snopack = DoubleField(null=True)
	pet = DoubleField(null=True)
	qtile = DoubleField(null=True)
	irr = DoubleField(null=True)
	surq_runon = DoubleField(null=True)
	latq_runon = DoubleField(null=True)
	overbank = DoubleField(null=True)
	surq_cha = DoubleField(null=True)
	surq_res = DoubleField(null=True)
	surq_ls = DoubleField(null=True)
	latq_cha = DoubleField(null=True)
	latq_res = DoubleField(null=True)
	latq_ls = DoubleField(null=True)
	gwtranq = DoubleField(null=True)
	satex = DoubleField(null=True)
	satex_chan = DoubleField(null=True)
	sw_change = DoubleField(null=True)
	lagsurf = DoubleField(null=True)
	laglatq = DoubleField(null=True)
	lagsatex = DoubleField(null=True)


class Basin_wb_day(Waterbal):
	pass


class Basin_wb_mon(Waterbal):
	pass


class Basin_wb_yr(Waterbal):
	pass


class Basin_wb_aa(Waterbal):
	pass


class Lsunit_wb_day(Waterbal):
	pass


class Lsunit_wb_mon(Waterbal):
	pass


class Lsunit_wb_yr(Waterbal):
	pass


class Lsunit_wb_aa(Waterbal):
	pass


class Hru_wb_day(Waterbal):
	pass


class Hru_wb_mon(Waterbal):
	pass


class Hru_wb_yr(Waterbal):
	pass


class Hru_wb_aa(Waterbal):
	pass


class Hru_lte_wb_day(Waterbal):
	pass


class Hru_lte_wb_mon(Waterbal):
	pass


class Hru_lte_wb_yr(Waterbal):
	pass


class Hru_lte_wb_aa(Waterbal):
	pass
