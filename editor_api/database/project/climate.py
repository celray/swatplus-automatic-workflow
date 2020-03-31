from peewee import *
from .base import BaseModel


class Weather_wgn_cli(BaseModel):
	name = CharField(unique=True)
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()
	rain_yrs = IntegerField()


class Weather_wgn_cli_mon(BaseModel):
	weather_wgn_cli = ForeignKeyField(Weather_wgn_cli, related_name='monthly_values', on_delete='CASCADE')
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


class Weather_sta_cli(BaseModel):
	name = CharField(unique=True)
	wgn = ForeignKeyField(Weather_wgn_cli, null=True, on_delete='SET NULL')
	pcp = CharField(null=True)
	tmp = CharField(null=True)
	slr = CharField(null=True)
	hmd = CharField(null=True)
	wnd = CharField(null=True)
	wnd_dir = CharField(null=True)
	atmo_dep = CharField(null=True)
	lat = DoubleField(null=True)
	lon = DoubleField(null=True)


class Weather_file(BaseModel):
	filename = CharField()
	type = CharField()
	lat = DoubleField()
	lon = DoubleField()


class Wind_dir_cli(BaseModel):
	name = CharField(unique=True)
	cnt = IntegerField()
	n = DoubleField()
	nne = DoubleField()
	ne = DoubleField()
	ene = DoubleField()
	e = DoubleField()
	ese = DoubleField()
	se = DoubleField()
	sse = DoubleField()
	s = DoubleField()
	ssw = DoubleField()
	sw = DoubleField()
	wsw = DoubleField()
	w = DoubleField()
	wnw = DoubleField()
	nw = DoubleField()
	nnw = DoubleField()


class Atmo_cli(BaseModel):
	filename = CharField()
	timestep = CharField()
	mo_init = IntegerField()
	yr_init = IntegerField()
	num_aa = IntegerField()


class Atmo_cli_sta(BaseModel):
	atmo_cli = ForeignKeyField(Atmo_cli, on_delete='CASCADE', related_name='stations')
	name = CharField()


class Atmo_cli_sta_value(BaseModel):
	sta = ForeignKeyField(Atmo_cli_sta, on_delete='CASCADE', related_name='values')
	timestep = IntegerField()
	nh4_wet = DoubleField()
	no3_wet = DoubleField()
	nh4_dry = DoubleField()
	no3_dry = DoubleField()
