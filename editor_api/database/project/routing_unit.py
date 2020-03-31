from peewee import *
from . import base, dr, hydrology

'''
Note: rout_unit.ele is defined in the connect section due to circular referencing of rout_unit_con and rout_unit_rtu

rout_unit.def
NUMB	 NAME		NSPU	HRU1	 HRU2
1		15		 3		 1	   -12	  17
2		16		 5		13	   -16	  21	  -25		27
3		25		 7		17	   -26	  29	   30		35	 37	  41
4		26		 2		27	   -28

The "-" indicates "through", e.g., HRUs 1 through 12 in NUMB 1.
NUMB 2 would mean HRUs 13-16, 21-25, and 27.

We really do not need rout_unit.def in the database.
Instead, add a FK to rout_unit_rtu.id in rout_unit_ele.
Get rid of def in rout_unit_rtu altogether!
'''


class Rout_unit_dr(base.BaseModel):
	name = CharField(unique=True)
	temp = DoubleField()
	flo = DoubleField()
	sed = DoubleField()
	orgn = DoubleField()
	sedp = DoubleField()
	no3 = DoubleField()
	solp = DoubleField()
	pest_sol = DoubleField()
	pest_sorb = DoubleField()
	chl_a = DoubleField()
	nh3 = DoubleField()
	no2 = DoubleField()
	cbn_bod = DoubleField()
	dis_ox = DoubleField()
	bact_p = DoubleField()
	bact_lp = DoubleField()
	met1 = DoubleField()
	met2 = DoubleField()
	met3 = DoubleField()
	san = DoubleField()
	sil = DoubleField()
	cla = DoubleField()
	sag = DoubleField()
	lag = DoubleField()
	grv = DoubleField()


class Rout_unit_rtu(base.BaseModel):
	name = CharField(unique=True)
	dlr = ForeignKeyField(Rout_unit_dr, null=True, on_delete='SET NULL')
	topo = ForeignKeyField(hydrology.Topography_hyd, null=True, on_delete='SET NULL')
	field = ForeignKeyField(hydrology.Field_fld, null=True, on_delete='SET NULL')
	description = TextField(null=True)
