from peewee import *
from . import base
from database import lib


class Gis_subbasins(base.BaseModel):
	area = DoubleField()
	slo1 = DoubleField()
	len1 = DoubleField()
	sll = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()
	elevmin = DoubleField()
	elevmax = DoubleField()


class Gis_channels(base.BaseModel):
	subbasin = IntegerField()
	areac = DoubleField()
	len2 = DoubleField()
	slo2 = DoubleField()
	wid2 = DoubleField()
	dep2 = DoubleField()
	elevmin = DoubleField()
	elevmax = DoubleField()


class Gis_lsus(base.BaseModel):
	category = IntegerField()
	channel = IntegerField()
	area = DoubleField()
	slope = DoubleField()
	csl = DoubleField()
	wid1 = DoubleField()
	dep1 = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()


class Gis_hrus(base.BaseModel):
	lsu = IntegerField()
	arsub = DoubleField()
	arlsu = DoubleField()
	landuse = CharField()
	arland = DoubleField()
	soil = CharField()
	arso = DoubleField()
	slp = CharField()
	arslp = DoubleField()
	slope = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()


class Gis_water(base.BaseModel):
	wtype = CharField()
	lsu = IntegerField()
	subbasin = IntegerField()
	area = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()


class Gis_points(base.BaseModel):
	subbasin = IntegerField()
	ptype = CharField()
	xpr = DoubleField()
	ypr = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField()


class Gis_routing(base.BaseModel):
	sourceid = PrimaryKeyField()
	sourcecat = CharField()
	sinkid = IntegerField()
	sinkcat = CharField()
	percent = DoubleField()

	@classmethod
	def find_from_sink(cls, sinkcat, sinkid):
		return cls.get_or_none((cls.sinkcat == sinkcat) & (cls.sinkid == sinkid))

	@classmethod
	def find_from_source(cls, sourcecat, sourceid):
		return cls.get_or_none((cls.sourcecat == sourcecat) & (cls.sourceid == sourceid))

	@classmethod
	def all_from_sink(cls, sinkcat, sinkid):
		return cls.select().where((cls.sinkcat == sinkcat) & (cls.sinkid == sinkid))

	@classmethod
	def all_from_source(cls, sourcecat, sourceid):
		return cls.select().where((cls.sourcecat == sourcecat) & (cls.sourceid == sourceid))
