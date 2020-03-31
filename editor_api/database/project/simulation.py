from peewee import *
from .base import BaseModel


class Time_sim(BaseModel):
	day_start = IntegerField()
	yrc_start = IntegerField()
	day_end = IntegerField()
	yrc_end = IntegerField()
	step = IntegerField()

	@classmethod
	def update_and_exec(cls, day_start, yrc_start, day_end, yrc_end, step):
		if cls.select().count() > 0:
			q = cls.update(day_start=day_start, yrc_start=yrc_start, day_end=day_end, yrc_end=yrc_end, step=step)
			return q.execute()
		else:
			v = cls.create(day_start=day_start, yrc_start=yrc_start, day_end=day_end, yrc_end=yrc_end, step=step)
			return 1 if v is not None else 0

	@classmethod
	def get_or_create_default(cls):
		if cls.select().count() > 0:
			return cls.get()

		return cls.create(day_start=0, yrc_start=1980, day_end=0, yrc_end=1985, step=0)


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


class Print_prt_aa_int(BaseModel):
	print_prt = ForeignKeyField(Print_prt, on_delete='CASCADE', related_name='aa_ints')
	year = IntegerField()


class Print_prt_object(BaseModel):
	print_prt = ForeignKeyField(Print_prt, on_delete='CASCADE', related_name='objects')
	name = CharField()
	daily = BooleanField()
	monthly = BooleanField()
	yearly = BooleanField()
	avann = BooleanField()


class Object_prt(BaseModel):
	ob_typ = CharField()
	ob_typ_no = IntegerField()
	hyd_typ = CharField()
	filename = CharField()


class Object_cnt(BaseModel):
	"""
	If the integer fields are set to 0, use the total - calculated programmatically.

	ls_area and tot_area not included below as they will be calculated.
	"""
	name = CharField()
	obj = IntegerField(default=0)
	hru = IntegerField(default=0)
	lhru = IntegerField(default=0)
	rtu = IntegerField(default=0)
	mfl = IntegerField(default=0)
	aqu = IntegerField(default=0)
	cha = IntegerField(default=0)
	res = IntegerField(default=0)
	rec = IntegerField(default=0)
	exco = IntegerField(default=0)
	dlr = IntegerField(default=0)
	can = IntegerField(default=0)
	pmp = IntegerField(default=0)
	out = IntegerField(default=0)
	lcha = IntegerField(default=0)
	aqu2d = IntegerField(default=0)
	hrd = IntegerField(default=0)
	wro = IntegerField(default=0)

	@classmethod
	def get_or_create_default(cls, project_name=None):
		if cls.select().count() > 0:
			q = cls.update(name=project_name)
			q.execute()
			return cls.get()

		return cls.create(name=project_name)


class Constituents_cs(BaseModel):
	name = CharField()
	pest_coms = CharField(null=True) # Comma-separated names from pesticides com?
	path_coms = CharField(null=True)
	hmet_coms = CharField(null=True)
	salt_coms = CharField(null=True)
