from peewee import *
from .base import BaseModel


class Wgn(BaseModel):
	name = CharField(unique=True)
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()
	rain_yrs = IntegerField()


class Wgn_mon(BaseModel):
	wgn = ForeignKeyField(Wgn, related_name='monthly_values', on_delete='CASCADE')
	month = IntegerField()
	tmp_max_ave = DoubleField()
	tmp_min_ave = DoubleField()
	tmp_max_sd = DoubleField()
	tmp_min_sd = DoubleField()
	pcp_ave = DoubleField()
	pcp_sd = DoubleField()
	pcp_skew = DoubleField()
	wet_dry = DoubleField()
	wet_wet = DoubleField()
	pcp_days = DoubleField()
	pcp_hhr = DoubleField()
	slr_ave = DoubleField()
	dew_ave = DoubleField()
	wnd_ave = DoubleField()
