from .base import BaseFileModel, FileColumn as col
from helpers import utils
import database.project.dr as db


class Dr_om_del(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		self.write_default_table(db.Dr_om_del, True)


class Delratio_del(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self, database='project'):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Delratio_del
		order_by = db.Delratio_del.id

		if table.select().count() > 0:
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

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.key_name_pad(row.om))
					file.write(utils.key_name_pad(row.pest))
					file.write(utils.key_name_pad(row.path))
					file.write(utils.key_name_pad(row.hmet))
					file.write(utils.key_name_pad(row.salt))
					file.write("\n")
