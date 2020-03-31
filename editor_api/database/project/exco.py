from peewee import *
from . import base


class Exco_om_exc(base.BaseModel):
	name = CharField(unique=True)
	flo = DoubleField()
	sed = DoubleField()
	orgn = DoubleField()
	sedp = DoubleField()
	no3 = DoubleField()
	solp = DoubleField()
	chla = DoubleField()
	nh3 = DoubleField()
	no2 = DoubleField()
	cbod = DoubleField()
	dox = DoubleField()
	sand = DoubleField()
	silt = DoubleField()
	clay = DoubleField()
	sag = DoubleField()
	lag = DoubleField()
	gravel = DoubleField()
	tmp = DoubleField()


class Exco_pest_exc(base.BaseModel):
	name = CharField(unique=True)


class Exco_pest_col(base.BaseModel):
	name = CharField(unique=True)


class Exco_pest_val(base.BaseModel):
	row = ForeignKeyField(Exco_pest_exc, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Exco_pest_col, null=True, on_delete='CASCADE')
	pest_sol = DoubleField()
	pest_sor = DoubleField()


class Exco_path_exc(base.BaseModel):
	name = CharField(unique=True)


class Exco_path_col(base.BaseModel):
	name = CharField(unique=True)


class Exco_path_val(base.BaseModel):
	row = ForeignKeyField(Exco_path_exc, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Exco_path_col, null=True, on_delete='CASCADE')
	path_sol = DoubleField()
	path_sor = DoubleField()


class Exco_hmet_exc(base.BaseModel):
	name = CharField(unique=True)


class Exco_hmet_col(base.BaseModel):
	name = CharField(unique=True)


class Exco_hmet_val(base.BaseModel):
	row = ForeignKeyField(Exco_hmet_exc, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Exco_hmet_col, null=True, on_delete='CASCADE')
	hmet_sol = DoubleField()
	hmet_sor = DoubleField()


class Exco_salt_exc(base.BaseModel):
	name = CharField(unique=True)


class Exco_salt_col(base.BaseModel):
	name = CharField(unique=True)


class Exco_salt_val(base.BaseModel):
	row = ForeignKeyField(Exco_salt_exc, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Exco_salt_col, null=True, on_delete='CASCADE')
	salt_sol = DoubleField()
	salt_sor = DoubleField()


class Exco_exc(base.BaseModel):
	name = CharField(unique=True)
	om = ForeignKeyField(Exco_om_exc, null=True, on_delete='SET NULL')
	pest = ForeignKeyField(Exco_pest_exc, null=True, on_delete='SET NULL')
	path = ForeignKeyField(Exco_path_exc, null=True, on_delete='SET NULL')
	hmet = ForeignKeyField(Exco_hmet_exc, null=True, on_delete='SET NULL')
	salt = ForeignKeyField(Exco_salt_exc, null=True, on_delete='SET NULL')
