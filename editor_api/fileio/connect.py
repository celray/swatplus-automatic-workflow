from helpers import utils, table_mapper
import database.project.connect as db

from database.project import hru, routing_unit, exco, reservoir, aquifer, channel, recall, dr
from .base import BaseFileModel


def write_header(file, elem_name, has_con_out):
	file.write(utils.int_pad("id"))
	file.write(utils.string_pad("name", direction="left"))
	file.write(utils.int_pad("gis_id"))
	file.write(utils.num_pad("area"))
	file.write(utils.num_pad("lat"))
	file.write(utils.num_pad("lon"))
	file.write(utils.num_pad("elev"))
	file.write(utils.int_pad(elem_name))
	file.write(utils.string_pad("wst"))
	file.write(utils.int_pad("cst"))
	file.write(utils.int_pad("ovfl"))
	file.write(utils.int_pad("rule"))
	file.write(utils.int_pad("out_tot"))

	if has_con_out:
		file.write(utils.code_pad("obj_typ"))
		file.write(utils.int_pad("obj_id"))
		file.write(utils.code_pad("hyd_typ"))
		file.write(utils.num_pad("frac"))

	file.write("\n")


def write_row(file, con, index, con_to_index, con_outs, con_out_id_dict):
	file.write(utils.int_pad(index))
	file.write(utils.string_pad(con.name, direction="left"))
	file.write(utils.int_pad(con.gis_id))
	file.write(utils.num_pad(con.area, use_non_zero_min=True))
	file.write(utils.num_pad(con.lat))
	file.write(utils.num_pad(con.lon))
	file.write(utils.num_pad(con.elev))
	file.write(utils.int_pad(con_to_index))
	file.write(utils.string_pad("null" if con.wst is None else con.wst.name))
	file.write(utils.int_pad(con.cst_id))
	file.write(utils.int_pad(con.ovfl))
	file.write(utils.int_pad(con.rule))
	file.write(utils.int_pad(con_outs.count()))

	for out in con_outs:
		obj_id = out.obj_id

		elem_table = table_mapper.obj_typs.get(out.obj_typ, None)
		if elem_table is not None:
			obj_id = con_out_id_dict[out.obj_typ].index(out.obj_id) + 1
			#obj_id = elem_table.select().where(elem_table.id <= out.obj_id).count()

		file.write(utils.code_pad(out.obj_typ))
		file.write(utils.int_pad(obj_id))
		file.write(utils.code_pad(out.hyd_typ))
		file.write(utils.num_pad(out.frac))

	file.write("\n")


def write_con_table(file_name, meta_line, con_table, con_out_table, elem_name, elem_table):
	if con_table.select().count() > 0:
		with open(file_name, 'w') as file:
			file.write(meta_line)
			write_header(file, elem_name, con_out_table.select().count() > 0)

			con_out_types = con_out_table.select(con_out_table.obj_typ).distinct()
			con_out_id_dict = {}
			for out_typ in con_out_types:
				obj_table = table_mapper.obj_typs.get(out_typ.obj_typ, None)
				con_out_id_dict[out_typ.obj_typ] = [o.id for o in obj_table.select(obj_table.id).order_by(obj_table.id)]

			elem_ids = [o.id for o in elem_table.select(elem_table.id).order_by(elem_table.id)]

			i = 1
			for con in con_table.select().order_by(con_table.id):
				elem_id = 1

				if elem_name == "hru":
					elem_id = con.hru_id
				elif elem_name == "rtu":
					elem_id = con.rtu_id
				elif elem_name == "aqu":
					elem_id = con.aqu_id
				elif elem_name == "cha":
					elem_id = con.cha_id
				elif elem_name == "res":
					elem_id = con.res_id
				elif elem_name == "rec":
					elem_id = con.rec_id
				elif elem_name == "exco":
					elem_id = con.exco_id
				elif elem_name == "lcha":
					elem_id = con.lcha_id
				elif elem_name == "lhru":
					elem_id = con.lhru_id

				con_to_index = elem_id
				if con.id != elem_id:
					con_to_index = elem_ids.index(elem_id) + 1
					#con_to_index = elem_table.select().where(elem_table.id <= elem_id).count()
				write_row(file, con, i, con_to_index, con.con_outs.order_by(con_out_table.order), con_out_id_dict)
				i += 1


class Hru_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Hru_con, db.Hru_con_out, "hru", hru.Hru_data_hru)


class Hru_lte_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Hru_lte_con, db.Hru_lte_con_out, "lhru", hru.Hru_lte_hru)


class Rout_unit_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Rout_unit_con, db.Rout_unit_con_out, "rtu", routing_unit.Rout_unit_rtu)


class Aquifer_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Aquifer_con, db.Aquifer_con_out, "aqu", aquifer.Aquifer_aqu)


class Channel_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Channel_con, db.Channel_con_out, "cha", channel.Channel_cha)


class Chandeg_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Chandeg_con, db.Chandeg_con_out, "lcha", channel.Channel_lte_cha)


class Reservoir_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Reservoir_con, db.Reservoir_con_out, "res", reservoir.Reservoir_res)


class Recall_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		#write_con_table(self.file_name, self.get_meta_line(), db.Recall_con, db.Recall_con_out, "rec", recall.Recall_rec)
		con_table = db.Recall_con
		con_out_table = db.Recall_con_out
		elem_table = recall.Recall_rec
		data = con_table.select(con_table, elem_table).join(elem_table).where(elem_table.rec_typ != 4)
		elem_data = elem_table.select(elem_table.id).where(elem_table.rec_typ != 4).order_by(elem_table.id)

		if data.count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				write_header(file, "rec", con_out_table.select().count() > 0)

				con_out_types = con_out_table.select(con_out_table.obj_typ).distinct()
				con_out_id_dict = {}
				for out_typ in con_out_types:
					obj_table = table_mapper.obj_typs.get(out_typ.obj_typ, None)
					con_out_id_dict[out_typ.obj_typ] = [o.id for o in obj_table.select(obj_table.id).order_by(obj_table.id)]

				elem_ids = [o.id for o in elem_data]

				i = 1
				for con in data.order_by(con_table.id):
					elem_id = con.rec_id
					con_to_index = elem_ids.index(elem_id) + 1
					write_row(file, con, i, con_to_index, con.con_outs.order_by(con_out_table.order), con_out_id_dict)
					i += 1


class Exco_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		#write_con_table(self.file_name, self.get_meta_line(), db.Exco_con, db.Exco_con_out, "exco", exco.Exco_exc)
		con_table = db.Recall_con
		con_out_table = db.Recall_con_out
		elem_table = recall.Recall_rec
		data_table = recall.Recall_dat
		#data = con_table.select(con_table, elem_table, data_table).join(elem_table).join(data_table).where((elem_table.rec_typ == 4) & (data_table.flo != 0))

		valid_recs = data_table.select(data_table.recall_rec_id).join(elem_table).where((elem_table.rec_typ == 4) & (data_table.flo != 0))
		valid_ids = [r.recall_rec_id for r in valid_recs]
		data = con_table.select(con_table, elem_table).join(elem_table).where(elem_table.id.in_(valid_ids))
		elem_data = elem_table.select(elem_table.id).where(elem_table.id.in_(valid_ids)).order_by(elem_table.id)

		if data.count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				write_header(file, "exco", con_out_table.select().count() > 0)

				con_out_types = con_out_table.select(con_out_table.obj_typ).distinct()
				con_out_id_dict = {}
				for out_typ in con_out_types:
					obj_table = table_mapper.obj_typs.get(out_typ.obj_typ, None)
					con_out_id_dict[out_typ.obj_typ] = [o.id for o in obj_table.select(obj_table.id).order_by(obj_table.id)]

				elem_ids = [o.id for o in elem_data]

				i = 1
				for con in data.order_by(con_table.id):
					elem_id = con.rec_id
					con_to_index = elem_ids.index(elem_id) + 1
					write_row(file, con, i, con_to_index, con.con_outs.order_by(con_out_table.order), con_out_id_dict)
					i += 1


class Delratio_con(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		write_con_table(self.file_name, self.get_meta_line(), db.Delratio_con, db.Delratio_con_out, "dlr", dr.Delratio_del)
