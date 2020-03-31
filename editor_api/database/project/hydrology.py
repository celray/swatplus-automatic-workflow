from peewee import *
from . import base


class Hydrology_hyd(base.BaseModel):
	name = CharField(unique=True)
	lat_ttime = DoubleField()
	lat_sed = DoubleField()
	can_max = DoubleField()
	esco = DoubleField()
	epco = DoubleField()
	orgn_enrich = DoubleField()
	orgp_enrich = DoubleField()
	cn3_swf = DoubleField()
	bio_mix = DoubleField()
	perco = DoubleField()
	lat_orgn = DoubleField()
	lat_orgp = DoubleField()
	harg_pet = DoubleField()
	latq_co = DoubleField()

	@staticmethod
	def get_perco_cn3_swf_latq_co(hyd_grp, slope, is_tile=False):
		leach_pot = 'low'
		runoff_pot = 'low'
		if not is_tile:
			if hyd_grp == 'A':
				leach_pot = 'high'
				runoff_pot = 'low' if slope < 6 else 'mod' if slope <= 12 else 'high'
			elif hyd_grp == 'B':
				leach_pot = 'high' if slope < 6 else 'mod'
				runoff_pot = 'low' if slope < 4 else 'mod' if slope <= 6 else 'high'
			elif hyd_grp == 'C':
				leach_pot = 'mod' if slope < 12 else 'low'
				runoff_pot = 'low' if slope < 2 else 'mod' if slope <= 6 else 'high'
			elif hyd_grp == 'D':
				leach_pot = 'low'
				runoff_pot = 'low' if slope < 2 else 'mod' if slope <= 4 else 'high'

		return {
			'perco': 0.9 if leach_pot == 'high' else 0.5 if leach_pot == 'mod' else 0.05,
			'cn3_swf': 0 if runoff_pot == 'high' else 0.3 if runoff_pot == 'mod' else 0.95,
			'latq_co': 0.9 if runoff_pot == 'high' else 0.2 if runoff_pot == 'mod' else 0.01
		}


class Topography_hyd(base.BaseModel):
	name = CharField(unique=True)
	slp = DoubleField()
	slp_len = DoubleField()
	lat_len = DoubleField()
	dist_cha = DoubleField()
	depos = DoubleField()
	type = CharField(null=True)  # sub or hru, for internal use; not in model - make this a drop-down in the editor!


class Field_fld(base.BaseModel):
	name = CharField(unique=True)
	len = DoubleField()
	wd = DoubleField()
	ang = DoubleField()
