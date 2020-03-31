from peewee import *
from .base import BaseModel


class Soil(BaseModel):
	name = CharField(unique=True)
	muid = CharField(null=True)
	seqn = IntegerField(null=True)
	s5id = CharField(null=True)
	cmppct = IntegerField(null=True)
	hydgrp = CharField()
	zmx = DoubleField()
	anion_excl = DoubleField()
	crk = DoubleField()
	texture = CharField(null=True)


class Soil_layer(BaseModel):
	soil = ForeignKeyField(Soil, on_delete='CASCADE')
	layer_num = IntegerField()
	z = DoubleField()
	bd = DoubleField()
	awc = DoubleField()
	k = DoubleField()
	cbn = DoubleField()
	clay = DoubleField()
	silt = DoubleField()
	sand = DoubleField()
	rock = DoubleField()
	alb = DoubleField()
	usle_k = DoubleField()
	ec = DoubleField()
	cal = DoubleField(null=True)
	ph = DoubleField(null=True)


class Soils_lte_sol(BaseModel):
	name = CharField(unique=True)
	awc = DoubleField()
	por = DoubleField()
	scon = DoubleField()
