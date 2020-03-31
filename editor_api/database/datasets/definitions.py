from peewee import *
from .base import BaseModel
import datetime


class Tropical_bounds(BaseModel):
	north = DoubleField()
	south = DoubleField()


class Version(BaseModel):
	value = CharField()
	release_date = DateTimeField(default=datetime.datetime.now)


class Var_code(BaseModel):
	table = CharField()
	variable = CharField()
	code = CharField()
	description = CharField()


class Var_range(BaseModel):
	table = CharField()
	variable = CharField()
	type = CharField()
	min_value = DoubleField()
	max_value = DoubleField()
	default_value = DoubleField()
	default_text = CharField(null=True)
	units = CharField(null=True)
	description = CharField(null=True)
	
	
class Var_range_option(BaseModel):
	var_range = ForeignKeyField(Var_range, on_delete='CASCADE', related_name='options')
	value = IntegerField()
	text = CharField()
	text_only = BooleanField()
	text_value = CharField(null=True)


class File_cio_classification(BaseModel):
	name = CharField()


class File_cio(BaseModel):
	classification = ForeignKeyField(File_cio_classification, on_delete='CASCADE', related_name='files')
	order_in_class = IntegerField()
	database_table = CharField()
	default_file_name = CharField()
	is_core_file = BooleanField()


class Print_prt(BaseModel):
	nyskip = IntegerField()
	day_start = IntegerField()
	yrc_start = IntegerField()
	day_end = IntegerField()
	yrc_end = IntegerField()
	interval = IntegerField()
	csvout = BooleanField()
	dbout = BooleanField()
	cdfout = BooleanField()
	soilout = BooleanField()
	mgtout = BooleanField()
	hydcon = BooleanField()
	fdcout = BooleanField()


class Print_prt_object(BaseModel):
	name = CharField()
	daily = BooleanField()
	monthly = BooleanField()
	yearly = BooleanField()
	avann = BooleanField()


class ColumnTypes:
	INT = "int"
	DOUBLE = "double"
	STRING = "string"


class TableNames:
	HYDROLOGY_CHA = "hydology_cha"
	TOPOGRAPHY_SUB = "topography_sub"
