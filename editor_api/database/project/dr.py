from peewee import *
from . import base


class Dr_om_del(base.BaseModel):
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


class Dr_pest_del(base.BaseModel):
	name = CharField(unique=True)


class Dr_pest_col(base.BaseModel):
	name = CharField(unique=True)


class Dr_pest_val(base.BaseModel):
	row = ForeignKeyField(Dr_pest_del, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Dr_pest_col, null=True, on_delete='CASCADE')
	pest_sol = DoubleField()
	pest_sor = DoubleField()


class Dr_path_del(base.BaseModel):
	name = CharField(unique=True)


class Dr_path_col(base.BaseModel):
	name = CharField(unique=True)


class Dr_path_val(base.BaseModel):
	row = ForeignKeyField(Dr_path_del, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Dr_path_col, null=True, on_delete='CASCADE')
	path_sol = DoubleField()
	path_sor = DoubleField()


class Dr_hmet_del(base.BaseModel):
	name = CharField(unique=True)


class Dr_hmet_col(base.BaseModel):
	name = CharField(unique=True)


class Dr_hmet_val(base.BaseModel):
	row = ForeignKeyField(Dr_hmet_del, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Dr_hmet_col, null=True, on_delete='CASCADE')
	hmet_sol = DoubleField()
	hmet_sor = DoubleField()


class Dr_salt_del(base.BaseModel):
	name = CharField(unique=True)


class Dr_salt_col(base.BaseModel):
	name = CharField(unique=True)


class Dr_salt_val(base.BaseModel):
	row = ForeignKeyField(Dr_salt_del, null=True, on_delete='CASCADE')
	col = ForeignKeyField(Dr_salt_col, null=True, on_delete='CASCADE')
	salt_sol = DoubleField()
	salt_sor = DoubleField()


class Delratio_del(base.BaseModel):
	name = CharField(unique=True)
	om = ForeignKeyField(Dr_om_del, null=True, on_delete='SET NULL')
	pest = ForeignKeyField(Dr_pest_del, null=True, on_delete='SET NULL')
	path = ForeignKeyField(Dr_path_del, null=True, on_delete='SET NULL')
	hmet = ForeignKeyField(Dr_hmet_del, null=True, on_delete='SET NULL')
	salt = ForeignKeyField(Dr_salt_del, null=True, on_delete='SET NULL')
