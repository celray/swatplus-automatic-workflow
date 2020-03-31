from peewee import *
from . import base


class Region_ele(base.BaseModel):
	name = CharField(unique=True)
	obj_typ = CharField()
	obj_typ_no = IntegerField()
	bsn_frac = DoubleField()
	sub_frac = DoubleField()
	reg_frac = DoubleField()


class Region_def(base.BaseModel):
	name = CharField(unique=True)
	area = DoubleField()


class Region_def_elem(base.BaseModel):
	elem = IntegerField()


"""
Landscape units
"""
class Ls_unit_def(Region_def):
	pass


class Ls_unit_ele(Region_ele):
	ls_unit_def = ForeignKeyField(Ls_unit_def, on_delete='CASCADE', related_name='elements')


"""
Landscape regions
"""
class Ls_reg_def(Region_def):
	pass


class Ls_reg_ele(Region_ele):
	ls_reg_def = ForeignKeyField(Ls_reg_def, on_delete='CASCADE', related_name='elements')


"""
Channel cataloging units
"""
class Ch_catunit_ele(Region_ele):
	pass


class Ch_catunit_def(Region_def):
	pass


class Ch_catunit_def_elem(Region_def_elem):
	ch_catunit_def = ForeignKeyField(Ch_catunit_def, on_delete='CASCADE', related_name='elements')


class Ch_reg_def(Region_def):
	pass


class Ch_reg_def_elem(Region_def_elem):
	ch_reg_def = ForeignKeyField(Ch_reg_def, on_delete='CASCADE', related_name='elements')


"""
Aquifer cataloging units
"""
class Aqu_catunit_ele(Region_ele):
	pass


class Aqu_catunit_def(Region_def):
	pass


class Aqu_catunit_def_elem(Region_def_elem):
	aqu_catunit_def = ForeignKeyField(Aqu_catunit_def, on_delete='CASCADE', related_name='elements')


class Aqu_reg_def(Region_def):
	pass


class Aqu_reg_def_elem(Region_def_elem):
	aqu_reg_def = ForeignKeyField(Aqu_reg_def, on_delete='CASCADE', related_name='elements')


"""
Reservoir cataloging units
"""
class Res_catunit_ele(Region_ele):
	pass


class Res_catunit_def(Region_def):
	pass


class Res_catunit_def_elem(Region_def_elem):
	res_catunit_def = ForeignKeyField(Res_catunit_def, on_delete='CASCADE', related_name='elements')


class Res_reg_def(Region_def):
	pass


class Res_reg_def_elem(Region_def_elem):
	res_reg_def = ForeignKeyField(Res_reg_def, on_delete='CASCADE', related_name='elements')


"""
Recall cataloging units
"""
class Rec_catunit_ele(Region_ele):
	pass


class Rec_catunit_def(Region_def):
	pass


class Rec_catunit_def_elem(Region_def_elem):
	rec_catunit_def = ForeignKeyField(Rec_catunit_def, on_delete='CASCADE', related_name='elements')


class Rec_reg_def(Region_def):
	pass


class Rec_reg_def_elem(Region_def_elem):
	rec_reg_def = ForeignKeyField(Rec_reg_def, on_delete='CASCADE', related_name='elements')
