from peewee import *
from .base import OutputBase


class Channel(OutputBase):
	flo_in = DoubleField(null=True)
	flo_out = DoubleField(null=True)
	evap = DoubleField(null=True)
	tloss = DoubleField(null=True)
	sed_in = DoubleField(null=True)
	sed_out = DoubleField(null=True)
	sed_conc = DoubleField(null=True)
	orgn_in = DoubleField(null=True)
	orgn_out = DoubleField(null=True)
	orgp_in = DoubleField(null=True)
	orgp_out = DoubleField(null=True)
	no3_in = DoubleField(null=True)
	no3_out = DoubleField(null=True)
	nh4_in = DoubleField(null=True)
	nh4_out = DoubleField(null=True)
	no2_in = DoubleField(null=True)
	no2_out = DoubleField(null=True)
	solp_in = DoubleField(null=True)
	solp_out = DoubleField(null=True)
	chla_in = DoubleField(null=True)
	chla_out = DoubleField(null=True)
	cbod_in = DoubleField(null=True)
	cbod_out = DoubleField(null=True)
	dis_in = DoubleField(null=True)
	dis_out = DoubleField(null=True)
	solpst_in = DoubleField(null=True)
	solpst_out = DoubleField(null=True)
	sorbpst_in = DoubleField(null=True)
	sorbpst_out = DoubleField(null=True)
	react = DoubleField(null=True)
	volat = DoubleField(null=True)
	setlpst = DoubleField(null=True)
	resuspst = DoubleField(null=True)
	difus = DoubleField(null=True)
	reactb = DoubleField(null=True)
	bury = DoubleField(null=True)
	sedpest = DoubleField(null=True)
	bacp = DoubleField(null=True)
	baclp = DoubleField(null=True)
	met1 = DoubleField(null=True)
	met2 = DoubleField(null=True)
	met3 = DoubleField(null=True)
	sand_in = DoubleField(null=True)
	sand_out = DoubleField(null=True)
	silt_in = DoubleField(null=True)
	silt_out = DoubleField(null=True)
	clay_in = DoubleField(null=True)
	clay_out = DoubleField(null=True)
	smag_in = DoubleField(null=True)
	smag_out = DoubleField(null=True)
	lag_in = DoubleField(null=True)
	lag_out = DoubleField(null=True)
	grvl_in = DoubleField(null=True)
	grvl_out = DoubleField(null=True)
	bnk_ero = DoubleField(null=True)
	ch_deg = DoubleField(null=True)
	ch_dep = DoubleField(null=True)
	fp_dep = DoubleField(null=True)
	tot_ssed = DoubleField(null=True)


class Basin_cha_day(Channel):
	pass


class Basin_cha_mon(Channel):
	pass


class Basin_cha_yr(Channel):
	pass


class Basin_cha_aa(Channel):
	pass


class Channel_day(Channel):
	pass


class Channel_mon(Channel):
	pass


class Channel_yr(Channel):
	pass


class Channel_aa(Channel):
	pass


class Channel_sdmorph(OutputBase):
	flo_in = DoubleField(null=True)
	geo_bf = DoubleField(null=True)
	flo_out = DoubleField(null=True)
	peakr = DoubleField(null=True)
	sed_in = DoubleField(null=True)
	sed_out = DoubleField(null=True)
	washld = DoubleField(null=True)
	bedld = DoubleField(null=True)
	dep = DoubleField(null=True)
	deg_btm = DoubleField(null=True)
	deg_bank = DoubleField(null=True)
	hc_sed = DoubleField(null=True)
	width = DoubleField(null=True)
	depth = DoubleField(null=True)
	slope = DoubleField(null=True)
	deg_btm_m = DoubleField(null=True)
	deg_bank_m = DoubleField(null=True)
	hc_len = DoubleField(null=True)
	flo_in_mm = DoubleField(null=True)
	aqu_in_mm = DoubleField(null=True)
	flo_out_mm = DoubleField(null=True)


class Basin_sd_chamorph_day(Channel_sdmorph):
	pass


class Basin_sd_chamorph_mon(Channel_sdmorph):
	pass


class Basin_sd_chamorph_yr(Channel_sdmorph):
	pass


class Basin_sd_chamorph_aa(Channel_sdmorph):
	pass


class Channel_sdmorph_day(Channel_sdmorph):
	pass


class Channel_sdmorph_mon(Channel_sdmorph):
	pass


class Channel_sdmorph_yr(Channel_sdmorph):
	pass


class Channel_sdmorph_aa(Channel_sdmorph):
	pass


class Channel_sd(OutputBase):
	area = DoubleField(null=True)
	precip = DoubleField(null=True)
	evap = DoubleField(null=True)
	seep = DoubleField(null=True)
	flo_stor = DoubleField(null=True)
	sed_stor = DoubleField(null=True)
	orgn_stor = DoubleField(null=True)
	sedp_stor = DoubleField(null=True)
	no3_stor = DoubleField(null=True)
	solp_stor = DoubleField(null=True)
	chla_stor = DoubleField(null=True)
	nh3_stor = DoubleField(null=True)
	no2_stor = DoubleField(null=True)
	cbod_stor = DoubleField(null=True)
	dox_stor = DoubleField(null=True)
	san_stor = DoubleField(null=True)
	sil_stor = DoubleField(null=True)
	cla_stor = DoubleField(null=True)
	sag_stor = DoubleField(null=True)
	lag_stor = DoubleField(null=True)
	grv_stor = DoubleField(null=True)
	temp_stor = DoubleField(null=True)
	flo_in = DoubleField(null=True)
	sed_in = DoubleField(null=True)
	orgn_in = DoubleField(null=True)
	sedp_in = DoubleField(null=True)
	no3_in = DoubleField(null=True)
	solp_in = DoubleField(null=True)
	chla_in = DoubleField(null=True)
	nh3_in = DoubleField(null=True)
	no2_in = DoubleField(null=True)
	cbod_in = DoubleField(null=True)
	dox_in = DoubleField(null=True)
	san_in = DoubleField(null=True)
	sil_in = DoubleField(null=True)
	cla_in = DoubleField(null=True)
	sag_in = DoubleField(null=True)
	lag_in = DoubleField(null=True)
	grv_in = DoubleField(null=True)
	temp_in = DoubleField(null=True)
	flo_out = DoubleField(null=True)
	sed_out = DoubleField(null=True)
	orgn_out = DoubleField(null=True)
	sedp_out = DoubleField(null=True)
	no3_out = DoubleField(null=True)
	solp_out = DoubleField(null=True)
	chla_out = DoubleField(null=True)
	nh3_out = DoubleField(null=True)
	no2_out = DoubleField(null=True)
	cbod_out = DoubleField(null=True)
	dox_out = DoubleField(null=True)
	san_out = DoubleField(null=True)
	sil_out = DoubleField(null=True)
	cla_out = DoubleField(null=True)
	sag_out = DoubleField(null=True)
	lag_out = DoubleField(null=True)
	grv_out = DoubleField(null=True)
	temp_out = DoubleField(null=True)
	water_temp = DoubleField(null=True)


class Basin_sd_cha_day(Channel_sd):
	pass


class Basin_sd_cha_mon(Channel_sd):
	pass


class Basin_sd_cha_yr(Channel_sd):
	pass


class Basin_sd_cha_aa(Channel_sd):
	pass


class Channel_sd_day(Channel_sd):
	pass


class Channel_sd_mon(Channel_sd):
	pass


class Channel_sd_yr(Channel_sd):
	pass


class Channel_sd_aa(Channel_sd):
	pass
