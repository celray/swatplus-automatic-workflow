from .base import BaseFileModel, FileColumn as col
import database.project.recall as db
from helpers import utils
import os.path
from database.project import base as project_base, simulation
from database import lib as db_lib
import csv
import datetime


class Recall_rec(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def read_data(self, recall_rec_id, delete_existing, rec_typ):
		with open(self.file_name, mode='r') as csv_file:
			dialect = csv.Sniffer().sniff(csv_file.readline())
			csv_file.seek(0)
			replace_commas = dialect is not None and dialect.delimiter != ','
			csv_reader = csv.DictReader(csv_file)
			rows = []

			"""
			recTypOptions: [
				{ value: 1, text: 'Daily' },
				{ value: 2, text: 'Monthly' },
				{ value: 3, text: 'Yearly' },
				{ value: 4, text: 'Constant' }
			]
			"""
			for row in csv_reader:
				if replace_commas:
					for key in row:
						row[key] = row[key].replace(',', '.', 1)
				row['recall_rec_id'] = recall_rec_id
				rows.append(row)

			if delete_existing:
				db.Recall_dat.delete().where(db.Recall_dat.recall_rec_id == recall_rec_id).execute()

			db_lib.bulk_insert(project_base.db, db.Recall_dat, rows)
			db.Recall_rec.update(rec_typ=rec_typ).where(db.Recall_rec.id == recall_rec_id).execute()

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
					row['jday'] = 0
					row['mo'] = 0
					row['day_mo'] = 0
					row['ob_typ'] = 'pt_cnst'
					row['ob_name'] = row['name']
					row.pop('name', None)
					rows.append(row)

			db_lib.bulk_insert(project_base.db, db.Recall_dat, rows)

	def write(self):
		table = db.Recall_rec
		order_by = db.Recall_rec.id
		data = table.select().where(table.rec_typ != 4)

		if data.count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.id),
						col(table.name, direction="left"),
						col(table.rec_typ),
						col("file", not_in_db=True, padding_override=utils.DEFAULT_STR_PAD, direction="left")]
				self.write_headers(file, cols)
				file.write("\n")

				i = 1
				for row in data.order_by(order_by):
					file_name = '{name}.rec'.format(name=row.name) if row.rec_typ != 4 else row.name
					file.write(utils.int_pad(i))
					file.write(utils.string_pad(row.name, direction="left"))
					file.write(utils.int_pad(row.rec_typ))
					file.write(utils.string_pad(file_name, direction="left"))
					file.write("\n")

					dir = os.path.dirname(self.file_name)
					self.write_data(row.data, os.path.join(dir, file_name))
					i += 1

	def write_data(self, data, file_name):
		table = db.Recall_dat
		with open(file_name, 'w') as file:
			time_sim = simulation.Time_sim.get()			
			valid_data = []
			for row in data.order_by(db.Recall_dat.yr, db.Recall_dat.jday, db.Recall_dat.id):
				valid_row = row.yr >= time_sim.yrc_start and row.yr <= time_sim.yrc_end
				rec_typ = row.recall_rec.rec_typ
				if valid_row and rec_typ == 1: #daily
					valid_row = (time_sim.day_start == 0 or row.jday >= time_sim.day_start) and (time_sim.day_end == 0 or row.jday <= time_sim.day_end)
				if valid_row and rec_typ == 2: #monthly
					rec_jday = datetime.datetime(row.yr, row.mo, 1).timetuple().tm_yday
					valid_row = (time_sim.day_start == 0 or rec_jday >= time_sim.day_start) and (time_sim.day_end == 0 or rec_jday <= time_sim.day_end)

				if valid_row:
					valid_data.append(row)

			file.write(self.get_meta_line())
			file.write(str(len(valid_data)))
			file.write("\n")

			cols = [
				col(table.jday),
				col(table.mo),
				col(table.day_mo),
				col(table.yr),
				col(table.ob_typ),
				col(table.ob_name),
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
				col(table.tmp)
			]

			self.write_headers(file, cols)
			file.write("\n")

			for row in valid_data:
				file.write(utils.int_pad(row.jday))
				file.write(utils.int_pad(row.mo))
				file.write(utils.int_pad(row.day_mo))
				file.write(utils.int_pad(row.yr))
				file.write(utils.string_pad(row.ob_typ))
				file.write(utils.string_pad(row.ob_name))
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
