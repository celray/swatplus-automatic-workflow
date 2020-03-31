from .base import BaseFileModel, FileColumn as col
import database.project.recall as db
from helpers import utils
import os.path
from database.project import base as project_base
from database import lib as db_lib
import csv


class Recall_rec(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def read_data(self, recall_rec_id, delete_existing):
		with open(self.file_name, mode='r') as csv_file:
			dialect = csv.Sniffer().sniff(csv_file.readline())
			csv_file.seek(0)
			replace_commas = dialect is not None and dialect.delimiter != ','
			csv_reader = csv.DictReader(csv_file)
			rows = []
			for row in csv_reader:
				if replace_commas:
					for key in row:
						row[key] = row[key].replace(',', '.', 1)
				row['recall_rec_id'] = recall_rec_id
				rows.append(row)

			if delete_existing:
				db.Recall_dat.delete().where(db.Recall_dat.recall_rec_id == recall_rec_id).execute()

			db_lib.bulk_insert(project_base.db, db.Recall_dat, rows)

	def read_const_data(self):
		with open(self.file_name, mode='r') as csv_file:
			dialect = csv.Sniffer().sniff(csv_file.readline())
			csv_file.seek(0)
			replace_commas = dialect is not None and dialect.delimiter != ','
			csv_reader = csv.DictReader(csv_file, dialect=dialect)
			rows = []
			for row in csv_reader:
				rec = db.Recall_rec.get_or_none(db.Recall_rec.name == row['name'])
				if rec is not None:
					db.Recall_rec.update(rec_typ=4).where(db.Recall_rec.id == rec.id).execute()
					db.Recall_dat.delete().where(db.Recall_dat.recall_rec_id == rec.id).execute()

					if replace_commas:
						for key in row:
							row[key] = row[key].replace(',', '.', 1)
					
					row['recall_rec_id'] = rec.id
					row['yr'] = 0
					row['t_step'] = 0
					row.pop('name', None)
					rows.append(row)

			db_lib.bulk_insert(project_base.db, db.Recall_dat, rows)

	def write(self):
		table = db.Recall_rec
		order_by = db.Recall_rec.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.id),
						col(table.name, direction="left"),
						col(table.rec_typ),
						col("file", not_in_db=True, padding_override=utils.DEFAULT_STR_PAD, direction="left")]
				self.write_headers(file, cols)
				file.write("\n")

				for row in table.select().order_by(order_by):
					file_name = '{name}.rec'.format(name=row.name) if row.rec_typ != 4 else row.name
					file.write(utils.int_pad(row.id))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.int_pad(row.rec_typ))
					file.write(utils.string_pad(file_name, direction="left"))
					file.write("\n")

					dir = os.path.dirname(self.file_name)
					if row.rec_typ != 4:
						self.write_data(row.data, os.path.join(dir, file_name))

	def write_data(self, data, file_name):
		table = db.Recall_dat
		with open(file_name, 'w') as file:
			file.write(self.get_meta_line())
			file.write(str(len(data)))
			file.write("\n")

			cols = [
				col(table.yr),
				col(table.t_step),
				col(table.flo),
				col(table.sed),
				col(table.ptl_n),
				col(table.ptl_p),
				col(table.no3_n),
				col(table.sol_p),
				col(table.chla),
				col(table.nh3_n),
				col(table.no2_n),
				col(table.cbn_bod),
				col(table.oxy),
				col(table.sand),
				col(table.silt),
				col(table.clay),
				col(table.sm_agg),
				col(table.lg_agg),
				col(table.gravel),
				col(table.tmp)
			]

			self.write_headers(file, cols)
			file.write("\n")
			
			for row in data.order_by(db.Recall_dat.yr, db.Recall_dat.t_step):
				file.write(utils.int_pad(row.yr))
				file.write(utils.int_pad(row.t_step))
				file.write(utils.num_pad(row.flo))
				file.write(utils.num_pad(row.sed))
				file.write(utils.num_pad(row.ptl_n))
				file.write(utils.num_pad(row.ptl_p))
				file.write(utils.num_pad(row.no3_n))
				file.write(utils.num_pad(row.sol_p))
				file.write(utils.num_pad(row.chla))
				file.write(utils.num_pad(row.nh3_n))
				file.write(utils.num_pad(row.no2_n))
				file.write(utils.num_pad(row.cbn_bod))
				file.write(utils.num_pad(row.oxy))
				file.write(utils.num_pad(row.sand))
				file.write(utils.num_pad(row.silt))
				file.write(utils.num_pad(row.clay))
				file.write(utils.num_pad(row.sm_agg))
				file.write(utils.num_pad(row.lg_agg))
				file.write(utils.num_pad(row.gravel))
				file.write(utils.num_pad(row.tmp))
				file.write("\n")
