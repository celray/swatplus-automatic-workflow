from peewee import *
from .base import BaseModel

class Soils_sol(BaseModel):
	name = CharField(unique=True)
	hyd_grp = CharField()
	dp_tot = DoubleField()
	anion_excl = DoubleField()
	perc_crk = DoubleField()
	texture = CharField(null=True)
	description = TextField(null=True)


class Soils_sol_layer(BaseModel):
	soil = ForeignKeyField(Soils_sol, on_delete='CASCADE', related_name='layers')
	layer_num = IntegerField()
	dp = DoubleField()
	bd = DoubleField()
	awc = DoubleField()
	soil_k = DoubleField()
	carbon = DoubleField()
	clay = DoubleField()
	silt = DoubleField()
	sand = DoubleField()
	rock = DoubleField()
	alb = DoubleField()
	usle_k = DoubleField()
	ec = DoubleField()
	caco3 = DoubleField(null=True)
	ph = DoubleField(null=True)


class Nutrients_sol(BaseModel):
	name = CharField(unique=True)
	dp_co = DoubleField()
	tot_n = DoubleField()
	min_n = DoubleField()
	org_n = DoubleField()
	tot_p = DoubleField()
	min_p = DoubleField()
	org_p = DoubleField()
	sol_p = DoubleField()
	h3a_p = DoubleField()
	mehl_p = DoubleField()
	bray_p = DoubleField()
	description = TextField(null=True)


class Soils_lte_sol(BaseModel):
	name = CharField(unique=True)
	awc = DoubleField()
	por = DoubleField()
	scon = DoubleField()
