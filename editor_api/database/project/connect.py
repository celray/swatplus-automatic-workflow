from peewee import *
from .base import BaseModel
from . import climate
from . import hru as hru_db
from . import routing_unit
from . import aquifer
from . import channel
from . import reservoir
from . import exco
from . import dr
from . import simulation
from . import recall


class Con(BaseModel):
	"""Inheritable base class for all connect files."""
	name = CharField(unique=True)
	gis_id = IntegerField(null=True)
	area = DoubleField()
	lat = DoubleField()
	lon = DoubleField()
	elev = DoubleField(null=True)
	wst = ForeignKeyField(climate.Weather_sta_cli, null=True, on_delete='SET NULL')
	cst = ForeignKeyField(simulation.Constituents_cs, null=True, on_delete='SET NULL')
	ovfl = IntegerField()  # ??? Pointer to the connections of spatial objects for overbank flooding
	rule = IntegerField()  # ??? Pointer to ruleset for flow fraction of hydrograph


class Con_out(BaseModel):
	"""Inheritable base class for all outflow parameters in many of the connect files."""
	order = IntegerField()
	obj_typ = CharField()
	obj_id = IntegerField()
	hyd_typ = CharField()
	frac = DoubleField()


class Hru_con(Con):
	hru = ForeignKeyField(hru_db.Hru_data_hru, null=True, on_delete='SET NULL')


class Hru_con_out(Con_out):
	hru_con = ForeignKeyField(Hru_con, on_delete='CASCADE', related_name='con_outs')


class Hru_lte_con(Con):
	lhru = ForeignKeyField(hru_db.Hru_lte_hru, null=True, on_delete='SET NULL')


class Hru_lte_con_out(Con_out):
	hru_lte_con = ForeignKeyField(Hru_lte_con, on_delete='CASCADE', related_name='con_outs')


class Rout_unit_con(Con):
	rtu = ForeignKeyField(routing_unit.Rout_unit_rtu, null=True, on_delete='SET NULL')


class Rout_unit_con_out(Con_out):
	rtu_con = ForeignKeyField(Rout_unit_con, on_delete ='CASCADE', related_name='con_outs')


class Modflow_con(Con):
	mfl = IntegerField()  # Should be FK to something, but no modflow object yet that I can find.


class Modflow_con_out(Con_out):
	modflow_con = ForeignKeyField(Modflow_con, on_delete='CASCADE', related_name='con_outs')


class Aquifer_con(Con):
	aqu = ForeignKeyField(aquifer.Aquifer_aqu, null=True, on_delete='SET NULL')


class Aquifer_con_out(Con_out):
	aquifer_con = ForeignKeyField(Aquifer_con, on_delete='CASCADE', related_name='con_outs')


class Aquifer2d_con(Con):
	aqu2d = ForeignKeyField(aquifer.Aquifer_aqu, null=True, on_delete='SET NULL') # Some doubt in documentation about this link


class Aquifer2d_con_out(Con_out):
	aquifer2d_con = ForeignKeyField(Aquifer2d_con, on_delete='CASCADE', related_name='con_outs')


class Channel_con(Con):
	cha = ForeignKeyField(channel.Channel_cha, null=True, on_delete='SET NULL')


class Channel_con_out(Con_out):
	channel_con = ForeignKeyField(Channel_con, on_delete='CASCADE', related_name='con_outs')


class Reservoir_con(Con):
	res = ForeignKeyField(reservoir.Reservoir_res, null=True, on_delete='SET NULL')


class Reservoir_con_out(Con_out):
	reservoir_con = ForeignKeyField(Reservoir_con, on_delete='CASCADE', related_name='con_outs')


class Recall_con(Con):
	rec = ForeignKeyField(recall.Recall_rec, null=True, on_delete='SET NULL')


class Recall_con_out(Con_out):
	recall_con = ForeignKeyField(Recall_con, on_delete='CASCADE', related_name='con_outs')


class Exco_con(Con):
	exco = ForeignKeyField(exco.Exco_exc, null=True, on_delete='SET NULL')


class Exco_con_out(Con_out):
	exco_con = ForeignKeyField(Exco_con, on_delete='CASCADE', related_name='con_outs')


class Delratio_con(Con):
	dlr = ForeignKeyField(dr.Delratio_del, null=True, on_delete='SET NULL')


class Delratio_con_out(Con_out):
	delratio_con = ForeignKeyField(Delratio_con, on_delete='CASCADE', related_name='con_outs')


class Outlet_con(Con):
	out = IntegerField() # Should be FK to something, but no outlet object yet that I can find.


class Outlet_con_out(Con_out):
	outlet_con = ForeignKeyField(Outlet_con, on_delete='CASCADE', related_name='con_outs')


class Chandeg_con(Con):
	lcha = ForeignKeyField(channel.Channel_lte_cha, null=True, on_delete='SET NULL')  


class Chandeg_con_out(Con_out):
	chandeg_con = ForeignKeyField(Chandeg_con, on_delete='CASCADE', related_name='con_outs')

# Though organized in the routing unit section, this needs to be here due to circular referencing of rout_unit_con and rout_unit_rtu
class Rout_unit_ele(BaseModel):
	name = CharField(unique=True)
	rtu = ForeignKeyField(Rout_unit_con, null=True, related_name='elements', on_delete='SET NULL')
	obj_typ = CharField()
	obj_id = IntegerField()
	frac = DoubleField()
	dlr = ForeignKeyField(dr.Delratio_del, null=True, on_delete='SET NULL')
