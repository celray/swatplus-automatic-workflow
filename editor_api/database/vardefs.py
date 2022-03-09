from peewee import *
import os

db = SqliteDatabase(None)


class BaseModel(Model):
	class Meta:
		database = db


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
	disabled = BooleanField()
	
	
class Var_range_option(BaseModel):
	var_range = ForeignKeyField(Var_range, on_delete='CASCADE', related_name='options')
	value = IntegerField()
	text = CharField()
	text_only = BooleanField()
	text_value = CharField(null=True)


class SetupVardefsDatabase():
	@staticmethod
	def init(datasets_db: str = None):
		db.init(datasets_db, pragmas={'journal_mode': 'off'})
