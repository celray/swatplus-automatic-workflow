from peewee import *
from .base import OutputBase, BaseModel


class HydBase(BaseModel):
	jday = IntegerField(null=True)
	mon = IntegerField(null=True)
	day = IntegerField(null=True)
	yr = IntegerField(null=True)
	#unit = IntegerField(null=True)
	#gis_id = IntegerField(null=True)
	name = CharField(null=True)
	type = CharField(null=True)
	objtyp = CharField(null=True)
	typ_no = IntegerField(null=True)
	hyd_typ = CharField(null=True)
	fraction = DoubleField(null=True)
	flo = DoubleField(null=True)
	sed = DoubleField(null=True)
	orgn = DoubleField(null=True)
	sedp = DoubleField(null=True)
	no3 = DoubleField(null=True)
	solp = DoubleField(null=True)
	chla = DoubleField(null=True)
	nh3 = DoubleField(null=True)
	no2 = DoubleField(null=True)
	cbod = DoubleField(null=True)
	dox = DoubleField(null=True)
	san = DoubleField(null=True)
	sil = DoubleField(null=True)
	cla = DoubleField(null=True)
	sag = DoubleField(null=True)
	lag = DoubleField(null=True)
	grv = DoubleField(null=True)
	temp = DoubleField(null=True)


class Hydout_day(HydBase):
	pass


class Hydout_mon(HydBase):
	pass


class Hydout_yr(HydBase):
	pass


class Hydout_aa(HydBase):
	pass


class Hydin_day(HydBase):
	pass


class Hydin_mon(HydBase):
	pass


class Hydin_yr(HydBase):
	pass


class Hydin_aa(HydBase):
	pass


class PtsBase(BaseModel):
	jday = IntegerField(null=True)
	mon = IntegerField(null=True)
	day = IntegerField(null=True)
	yr = IntegerField(null=True)
	#unit = IntegerField(null=True)
	#gis_id = IntegerField(null=True)
	name = CharField(null=True)
	type = CharField(null=True)
	flo = DoubleField(null=True)
	sed = DoubleField(null=True)
	orgn = DoubleField(null=True)
	sedp = DoubleField(null=True)
	no3 = DoubleField(null=True)
	solp = DoubleField(null=True)
	chla = DoubleField(null=True)
	nh3 = DoubleField(null=True)
	no2 = DoubleField(null=True)
	cbod = DoubleField(null=True)
	dox = DoubleField(null=True)
	san = DoubleField(null=True)
	sil = DoubleField(null=True)
	cla = DoubleField(null=True)
	sag = DoubleField(null=True)
	lag = DoubleField(null=True)
	grv = DoubleField(null=True)
	temp = DoubleField(null=True)


class PtsNoTypeBase(BaseModel):
	jday = IntegerField(null=True)
	mon = IntegerField(null=True)
	day = IntegerField(null=True)
	yr = IntegerField(null=True)
	#unit = IntegerField(null=True)
	#gis_id = IntegerField(null=True)
	name = CharField(null=True)
	#type = CharField(null=True)
	flo = DoubleField(null=True)
	sed = DoubleField(null=True)
	orgn = DoubleField(null=True)
	sedp = DoubleField(null=True)
	no3 = DoubleField(null=True)
	solp = DoubleField(null=True)
	chla = DoubleField(null=True)
	nh3 = DoubleField(null=True)
	no2 = DoubleField(null=True)
	cbod = DoubleField(null=True)
	dox = DoubleField(null=True)
	san = DoubleField(null=True)
	sil = DoubleField(null=True)
	cla = DoubleField(null=True)
	sag = DoubleField(null=True)
	lag = DoubleField(null=True)
	grv = DoubleField(null=True)
	temp = DoubleField(null=True)


class Basin_psc_day(PtsNoTypeBase):
	pass


class Basin_psc_mon(PtsNoTypeBase):
	pass


class Basin_psc_yr(PtsNoTypeBase):
	pass


class Basin_psc_aa(PtsNoTypeBase):
	pass


class Ru_day(PtsBase):
	pass


class Ru_mon(PtsBase):
	pass


class Ru_yr(PtsBase):
	pass


class Ru_aa(PtsBase):
	pass


class Deposition_day(PtsBase):
	pass


class Deposition_mon(PtsBase):
	pass


class Deposition_yr(PtsBase):
	pass


class Deposition_aa(PtsBase):
	pass


class Recall_day(PtsBase):
	pass


class Recall_mon(PtsBase):
	pass


class Recall_yr(PtsBase):
	pass


class Recall_aa(PtsBase):
	pass
