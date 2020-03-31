from peewee import *
from . import base


class Recall_rec(base.BaseModel):
	name = CharField(unique=True)
	rec_typ = IntegerField()  # 1-day, 2-mon, 3-yr, 4-const


class Recall_dat(base.BaseModel):
	recall_rec = ForeignKeyField(Recall_rec, on_delete='CASCADE', related_name='data')
	yr = IntegerField()
	t_step = IntegerField()
	flo = DoubleField()
	sed = DoubleField()
	ptl_n = DoubleField()
	ptl_p = DoubleField()
	no3_n = DoubleField()
	sol_p = DoubleField()
	#sol_pest = DoubleField()
	#srb_pest = DoubleField()
	chla = DoubleField()
	nh3_n = DoubleField()
	no2_n = DoubleField()
	cbn_bod = DoubleField()
	oxy = DoubleField()
	#p_bact = DoubleField()
	#lp_bact = DoubleField()
	#metl1 = DoubleField()
	#metl2 = DoubleField()
	#metl3 = DoubleField()
	sand = DoubleField()
	silt = DoubleField()
	clay = DoubleField()
	sm_agg = DoubleField()
	lg_agg = DoubleField()
	gravel = DoubleField()
	tmp = DoubleField()
