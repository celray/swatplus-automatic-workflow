from .base import BaseFileModel, FileColumn as col
from helpers import utils
from database.project.recall import Recall_dat, Recall_rec
import database.project.exco as db


class Exco_om_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		#self.write_default_table(db.Exco_om_exc, True)
		table = db.Exco_om_exc
		order_by = db.Exco_om_exc.id
		#recall_recs = Recall_rec.select(Recall_rec, Recall_dat).join(Recall_dat).where((Recall_rec.rec_typ == 4) & (Recall_dat.flo != 0))
		valid_recs = Recall_dat.select(Recall_dat.recall_rec_id).join(Recall_rec).where((Recall_rec.rec_typ == 4) & (Recall_dat.flo != 0))
		valid_ids = [r.recall_rec_id for r in valid_recs]
		recall_recs = Recall_rec.select().where(Recall_rec.id.in_(valid_ids))

		if recall_recs.count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.name, direction="left"),
						col(table.flo),
						col(table.sed),
						col(table.orgn),
						col(table.sedp),
						col(table.no3),
						col(table.solp),
						col(table.chla),
						col(table.nh3),
						col(table.no2),
						col(table.cbod),
						col(table.dox),
						col(table.sand),
						col(table.silt),
						col(table.clay),
						col(table.sag),
						col(table.lag),
						col(table.gravel),
						col(table.tmp)]
				self.write_headers(file, cols)
				file.write("\n")

				"""for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.num_pad(row.flo))
					file.write(utils.num_pad(row.sed))
					file.write(utils.num_pad(row.orgn))
					file.write(utils.num_pad(row.sedp))
					file.write(utils.num_pad(row.no3))
					file.write(utils.num_pad(row.solp))
					file.write(utils.num_pad(row.chla))
					file.write(utils.num_pad(row.nh3))
					file.write(utils.num_pad(row.no2))
					file.write(utils.num_pad(row.cbod))
					file.write(utils.num_pad(row.dox))
					file.write(utils.num_pad(row.sand))
					file.write(utils.num_pad(row.silt))
					file.write(utils.num_pad(row.clay))
					file.write(utils.num_pad(row.sag))
					file.write(utils.num_pad(row.lag))
					file.write(utils.num_pad(row.gravel))
					file.write(utils.num_pad(row.tmp))
					file.write("\n")"""

				for rec in recall_recs:
					row = Recall_dat.get_or_none((Recall_dat.recall_rec_id == rec.id) & (Recall_dat.flo != 0))
					if row is not None:
						file.write(utils.string_pad(rec.name, direction="left"))
						file.write(utils.num_pad(row.flo))
						file.write(utils.num_pad(row.sed))
						file.write(utils.num_pad(row.orgn))
						file.write(utils.num_pad(row.sedp))
						file.write(utils.num_pad(row.no3))
						file.write(utils.num_pad(row.solp))
						file.write(utils.num_pad(row.chla))
						file.write(utils.num_pad(row.nh3))
						file.write(utils.num_pad(row.no2))
						file.write(utils.num_pad(row.cbod))
						file.write(utils.num_pad(row.dox))
						file.write(utils.num_pad(row.sand))
						file.write(utils.num_pad(row.silt))
						file.write(utils.num_pad(row.clay))
						file.write(utils.num_pad(row.sag))
						file.write(utils.num_pad(row.lag))
						file.write(utils.num_pad(row.gravel))
						file.write(utils.num_pad(row.tmp))
						file.write("\n")


class Exco_pest_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Exco_pest_exc, True)


class Exco_path_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Exco_path_exc, True)


class Exco_hmet_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Exco_hmet_exc, True)


class Exco_salt_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Exco_salt_exc, True)


class Exco_exc(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Exco_exc
		order_by = db.Exco_exc.id

		valid_recs = Recall_dat.select(Recall_dat.recall_rec_id).join(Recall_rec).where((Recall_rec.rec_typ == 4) & (Recall_dat.flo != 0))
		valid_ids = [r.recall_rec_id for r in valid_recs]
		recall_recs = Recall_rec.select().where(Recall_rec.id.in_(valid_ids))
		#recall_recs = Recall_rec.select(Recall_rec, Recall_dat).join(Recall_dat).where((Recall_rec.rec_typ == 4) & (Recall_dat.flo != 0))

		if recall_recs.count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.name, direction="left"),
						col(table.om),
						col(table.pest),
						col(table.path),
						col(table.hmet),
						col(table.salt)]
				self.write_headers(file, cols)
				file.write("\n")

				"""for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.om))
					file.write(utils.key_name_pad(row.pest))
					file.write(utils.key_name_pad(row.path))
					file.write(utils.key_name_pad(row.hmet))
					file.write(utils.key_name_pad(row.salt))
					file.write("\n")"""

				for row in recall_recs:
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.string_pad(row.name))
					file.write(utils.key_name_pad(None))
					file.write(utils.key_name_pad(None))
					file.write(utils.key_name_pad(None))
					file.write(utils.key_name_pad(None))
					file.write("\n")
