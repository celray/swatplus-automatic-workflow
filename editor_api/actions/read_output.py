from helpers.executable_api import ExecutableApi, Unbuffered
from database.output.setup import SetupOutputDatabase
from database.output.aquifer import *
from database.output.channel import *
from database.output.hyd import *
from database.output.losses import *
from database.output.misc import *
from database.output.nutbal import *
from database.output.plantwx import *
from database.output.reservoir import *
from database.output.waterbal import *
from database.output import base
from database import lib as db_lib

import sys
import argparse
import os, os.path
import csv

default_start_line = 4
default_units_column_index = 7

special_start_lines = {
	'crop_yld': 6,
	'basin_crop_yld': 3,
	'soil_nutcarb_out': 3,
	'flow_duration_curve': 3,
	'hru_pest': 3,
	'basin_ls_pest': 3,
	'basin_ch_pest': 3,
	'basin_res_pest': 3,
	'channel_pest': 3,
	'reservoir_pest': 3,
	'basin_aqu_pest': 3,
	'aquifer_pest': 3
}

ignore_units = [
	'crop_yld',
	'soil_nutcarb_out',
	'flow_duration_curve',
	'hru_pest',
	'basin_ls_pest',
	'basin_ch_pest',
	'basin_res_pest',
	'channel_pest',
	'reservoir_pest',
	'basin_aqu_pest',
	'aquifer_pest'
]

units_start_column_index = {
	'basin_psc': 6,
	'region_psc': 6,
	'recall': 6,
	'hydin': 10,
	'hydout': 10,
	'ru': 6,
	'deposition': 6,
	'mgt_out': 0
}

"""reversed_unit_lines = [
	'basin_sd_cha',
	'basin_res',
	'channel_sd',
	'wetland'
]"""
reversed_unit_lines = []

table_labels = {
	'basin_wb': 'basin water balance',
	'basin_nb': 'basin nutrient balance',
	'basin_ls': 'basin losses',
	'basin_pw': 'basin plant weather',
	'basin_aqu': 'basin aquifer',
	'basin_res': 'basin reservoir',
	'basin_cha': 'basin channel',
	'basin_sd_cha': 'basin channel water balance, incoming/outgoing sediment and nutrients and storage',
	'basin_psc': 'basin point source',
	'region_wb': 'region water balance',
	'region_nb': 'region nutrient balance',
	'region_ls': 'region losses',
	'region_pw': 'region plant weather',
	'region_aqu': 'region aquifer',
	'region_res': 'region reservoir',
	'region_cha': 'region channel',
	'region_sd_cha': 'region channel',
	'region_psc': 'region point source',
	'lsunit_wb': 'routing unit water balance',
	'lsunit_nb': 'routing unit nutrient balance',
	'lsunit_ls': 'routing unit losses',
	'lsunit_pw': 'routing unit plant weather',
	'hru_wb': 'HRU water balance',
	'hru_nb': 'HRU nutrient balance',
	'hru_ls': 'HRU losses',
	'hru_pw': 'HRU plant weather',
	'hru_lte_wb': 'HRU-LTE water balance',
	'hru_lte_nb': 'HRU-LTE nutrient balance',
	'hru_lte_ls': 'HRU-LTE losses',
	'hru_lte_pw': 'HRU-LTE plant weather',
	'channel': 'channel',
	'channel_sd': 'channel water balance, incoming/outgoing sediment and nutrients and storage',
	'aquifer': 'aquifer',
	'reservoir': 'reservoir',
	'recall': 'point source (recall)',
	'hydin': 'hydrology in',
	'hydout': 'hydrology out',
	'ru': 'routing unit',
	'pest': 'pesticide constituents',
	'crop_yld': 'crop yield',
	'soil_nutcarb_out': 'soil nutrients carbon',
	'flow_duration_curve': 'flow duration curve',
	'mgt_out': 'management',
	'deposition': 'deposition',
	'channel_sdmorph' : 'channel morphology and sediment budget',
	'basin_sd_chamorph' : 'basin channel morphology and sediment budget',
	'basin_crop_yld': 'basin crop yield',
	'hru_pest': 'HRU pesticides',
	'basin_ls_pest': 'basin landscape unit pesticides',
	'basin_ch_pest': 'basin channel pesticides',
	'basin_res_pest': 'basin reservoir pesticides',
	'channel_pest': 'channel pesticides',
	'reservoir_pest': 'reservoir pesticides',
	'basin_aqu_pest': 'basin aquifer pesticides',
	'aquifer_pest': 'aquifer pesticides'
}

time_series_labels = {
	'day': 'daily',
	'mon': 'monthly',
	'yr': 'yearly',
	'aa': 'avg. annual'
}


class ReadOutput(ExecutableApi):
	def __init__(self, output_files_dir, db_file):
		self.__abort = False
		try:
			os.remove(db_file)
		except:
			pass  # try to remove file, but don't report an error if it fails.

		SetupOutputDatabase.init(db_file.replace("\\","/"))
		self.output_files_dir = output_files_dir.replace("\\","/")

	def read(self):
		self.setup_meta_tables()
		files_out_file = os.path.join(self.output_files_dir, 'files_out.out')
		dot_out_files_to_read = [
			'crop_yld_aa.out',
			'flow_duration_curve.out'
		]

		files = []

		try:
			with open(files_out_file, "r") as file:
				i = 1
				for line in file:
					if i > 1:
						val = line.split()
						if len(val) < 2:
							raise ValueError('Unexpected number of columns in {}'.format(files_out_file))

						file_name = val[len(val)-1].strip()
						if file_name.endswith('.txt') or file_name in dot_out_files_to_read:
							files.append(file_name)

					i += 1
		except FileNotFoundError:
			sys.exit('Could not find file, {}'.format(files_out_file))
		except ValueError as ve:
			sys.exit(ve)

		prog_step = 0 if len(files) < 1 else round(100 / len(files))
		prog = 0
		for file in files:
			name = file[:-4].replace('hru-lte', 'hru_lte')
			table_name = name[:1].upper() + name[1:]
			try:
				self.emit_progress(prog, 'Importing {}...'.format(file))

				desc_key = name
				time_series_key = ''
				for key in time_series_labels:
					desc_key = desc_key.replace('_{}'.format(key), '')
					if key in name:
						time_series_key = key

				description = '{ts} {n}'.format(ts=time_series_labels.get(time_series_key, ''), n=table_labels.get(desc_key, name))
				base.Table_description.insert(table_name=name, description=description).execute()

				table_class = globals()[table_name]
				base.db.create_tables([table_class])
				table_class.delete().execute()

				file_path = os.path.join(self.output_files_dir, file)
				self.read_default_table(file_path, name, table_class, base.db, start_line=special_start_lines.get(desc_key, default_start_line), desc_key=desc_key)
				prog += prog_step
			except KeyError as e:
				sys.exit('Table {table} does not exist: {e}'.format(table=table_name, e=e))
			except ValueError as e:
				sys.exit('Error importing {file}: {e}'.format(file=file, e=e))

	def read_default_table(self, file_name, name, table, db, start_line, ignore_id_col=True, desc_key=''):
		file = open(file_name, 'r')
		read_units = False if desc_key in ignore_units else True

		i = 1
		rows = []
		fields = table._meta.sorted_fields
		file_fields = []
		for line in file:
			if read_units and i == start_line - 2:
				for h in line.strip().split():
					file_fields.append(h.strip())
			elif read_units and i == start_line - 1:
				units = line.strip().split()
				ui = units_start_column_index.get(desc_key, default_units_column_index)
				reverse_index = True if desc_key in reversed_unit_lines else False
				col_descs = []
				for x in range(0, len(units)):					
					try:
						column_name_val = file_fields[x] if reverse_index else file_fields[ui + x]
						units_val = units[ui + x] if reverse_index else units[x]

						col_desc = {
							'table_name': name,
							'column_name': column_name_val,
							'units': units_val
						}
						col_descs.append(col_desc)
					except IndexError:
						pass
				db_lib.bulk_insert(db, base.Column_description, col_descs)
			elif i >= start_line:
				val = line.strip().split()

				row = {}
				j = 0
				for field in fields:
					skip = False
					if ignore_id_col and field.name == 'id':
						skip = True

					if not skip:
						try:
							row[field.name] = None if j >= len(val) or '*' in str(val[j]) else val[j]
						except IndexError:
							pass
						j += 1
				rows.append(row)

				if len(rows) == 1000:
					db_lib.bulk_insert(db, table, rows)
					rows = []
			i += 1

		db_lib.bulk_insert(db, table, rows)

	def setup_meta_tables(self):
		base.db.create_tables([
			base.Table_description, base.Column_description
		])

		base.Table_description.delete().execute()
		base.Column_description.delete().execute()


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description='Create the SWAT+ output database')
	parser.add_argument('output_files_dir', type=str, help='full path of output files directory')
	parser.add_argument('db_file', type=str, help='full path of output SQLite database file')
	args = parser.parse_args()

	api = ReadOutput(args.output_files_dir, args.db_file)
	api.read()
