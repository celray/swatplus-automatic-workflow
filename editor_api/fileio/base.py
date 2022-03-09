from abc import ABCMeta, abstractmethod
from peewee import *
from playhouse.shortcuts import model_to_dict
import time
import ntpath
import csv
from helpers import utils, table_mapper
from database import lib as db_lib
from enum import Enum


class FileOverwrite(Enum):
	ignore = 1
	replace = 2
	rename = 3


def write_csv(file_name, table, ignore_id_col=False, ignored_cols=[], custom_query=None, initial_headers=[]):
	with open(file_name, mode='w') as file:
		csv_writer = csv.writer(file, delimiter=',', lineterminator='\n', quotechar='"', quoting=csv.QUOTE_MINIMAL)

		headers = initial_headers
		for field in table._meta.sorted_fields:
			if not ignore_id_col or field.name != "id":
				if field.name not in ignored_cols:
					headers.append(field.name)

		csv_writer.writerow(headers)

		query = table.select().order_by(table.id)
		if custom_query is not None:
			query = custom_query.order_by(table.id)
			
		for row in query.dicts():
			values = []
			for col in headers:
				values.append(row[col])
			csv_writer.writerow(values)


def read_csv_file(file_name, table, db, expected_cols, ignore_id_col=False, convert_name_to_lower=False, overwrite=FileOverwrite.ignore, remove_spaces_cols=[]):
	csv_file = open(file_name, "r")

	dialect = csv.Sniffer().sniff(csv_file.readline())
	csv_file.seek(0)
	replace_commas = dialect is not None and dialect.delimiter != ','
	hasHeader = csv.Sniffer().has_header(csv_file.readline())
	csv_file.seek(0)

	csv_reader = csv.reader(csv_file, dialect)

	if hasHeader:
		headerLine = next(csv_reader)

	i = 1
	rows = []
	fields = table._meta.sorted_fields
	for val in csv_reader:
		if expected_cols > 0 and len(val) < expected_cols:
			raise IndexError(
				'Improperly formatted %s file. Expecting %s columns. Please refer to the SWAT+ IO documentation.' % (ntpath.basename(file_name), expected_cols))
		
		if replace_commas:
			val = [item.replace(',', '.', 1) for item in val]

		row = {}
		j = 0
		for field in fields:
			skip = False
			if ignore_id_col and field.name == "id":
				skip = True

			if not skip:
				value = None
				if len(val) > j:
					if convert_name_to_lower and field.name == "name":
						value = val[j].lower()
					elif field.name == "description":
						value = val[j] if val[j] != 'null' else None
					else:
						value = val[j]

				if type(value) is str:
					if value == 'null':
						value = None
				
				row[field.name] = value if field.name not in remove_spaces_cols else utils.remove_space(value)

				j += 1

		add_row = True
		if overwrite != FileOverwrite.ignore:
			try:
				m = table.get(table.name == row['name'])

				if overwrite == FileOverwrite.replace:
					query = table.update(row).where(table.id == m.id)
					result = query.execute()
					add_row = False
				elif overwrite == FileOverwrite.rename:
					k = 1
					while table.select().where(table.name == '{name}{num}'.format(name=row['name'], num=k)).exists():
						k += 1

					row['name'] = '{name}{num}'.format(name=row['name'], num=k)
			except table.DoesNotExist:
				pass

		if add_row:
			rows.append(row)

	db_lib.bulk_insert(db, table, rows)


def read_file(file_name, table, db, expected_cols, ignore_id_col=False, start_line=3, csv=False, convert_name_to_lower=False, overwrite=FileOverwrite.ignore, remove_spaces_cols=[]):
	file = open(file_name, "r")

	if csv:
		start_line = 2

	i = 1
	rows = []
	fields = table._meta.sorted_fields
	for line in file:
		if i >= start_line:
			val = line.split() if not csv else line.split(',')
			if expected_cols > 0 and len(val) < expected_cols:
				raise IndexError(
					'Improperly formatted %s file. Expecting %s columns. Please refer to the SWAT+ IO documentation.' % (ntpath.basename(file_name), expected_cols))

			row = {}
			j = 0
			for field in fields:
				skip = False
				if ignore_id_col and field.name == "id":
					skip = True

				if not skip:
					value = None
					if len(val) > j:
						if convert_name_to_lower and field.name == "name":
							value = val[j].lower()
						elif field.name == "description":
							value = val[j] if val[j] != 'null' else None
						else:
							value = val[j]

					if type(value) is str:
						value = value.replace('"', '')
						if value == 'null':
							value = None
					
					row[field.name] = value if field.name not in remove_spaces_cols else utils.remove_space(value)

					j += 1

			add_row = True
			if overwrite != FileOverwrite.ignore:
				try:
					m = table.get(table.name == row['name'])

					if overwrite == FileOverwrite.replace:
						query = table.update(row).where(table.id == m.id)
						result = query.execute()
						add_row = False
					elif overwrite == FileOverwrite.rename:
						k = 1
						while table.select().where(table.name == '{name}{num}'.format(name=row['name'], num=k)).exists():
							k += 1

						row['name'] = '{name}{num}'.format(name=row['name'], num=k)
				except table.DoesNotExist:
					pass

			if add_row:
				rows.append(row)
			
		i += 1

	db_lib.bulk_insert(db, table, rows)


class BaseFileModel:
	__metaclass__ = ABCMeta

	def __init(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	@abstractmethod
	def read(self): pass

	@abstractmethod
	def write(self): pass

	def check_cols(self, cols, num_expecting, file_name):
		if len(cols) < num_expecting:
			raise IndexError(
				'Improperly formatted %s file. Expecting %s columns. Please refer to the SWAT+ IO documentation.' % (file_name, num_expecting))

	def get_meta_line(self, alt_file_name=""):
		vtxt = ""
		if self.version is not None:
			vtxt = " v{version}".format(version=self.version)

		svtxt = ""
		if self.swat_version is not None:
			svtxt = "for SWAT+ rev.{swat_version}".format(swat_version=self.swat_version)

		name = self.file_name if alt_file_name == "" else alt_file_name

		return "{file}: written by SWAT+ editor{version} on {date} {swat_version}\n".format(file=ntpath.basename(name), version=vtxt, date=time.strftime("%Y-%m-%d %H:%M"), swat_version=svtxt)

	def write_meta_line(self, file, alt_file_name=""):
		file.write(self.get_meta_line(alt_file_name=alt_file_name))

	def write_headers(self, file, cols):
		for file_col in cols:
			if file_col.not_in_db:
				if file_col.padding_override is not None:
					utils.write_string(file, file_col.value, default_pad=file_col.padding_override, direction=file_col.direction)
				else:
					utils.write_string(file, file_col.value, direction=file_col.direction)
			else:
				db_col = file_col.value
				name = db_col.name

				# if not file_col.is_desc:
				if file_col.alt_header_name != "":
					name = file_col.alt_header_name
				elif file_col.query_alias != "":
					name = file_col.query_alias
				elif db_col.verbose_name is not None:
					name = db_col.verbose_name

				name = name.lower()

				if file_col.repeat is not None:
					name += str(file_col.repeat)

				if file_col.is_desc:
					utils.write_desc_string(file, name)
				elif file_col.padding_override is not None:
					utils.write_string(file, name, default_pad=file_col.padding_override, direction=file_col.direction)
				elif isinstance(db_col, ForeignKeyField):
					utils.write_string(file, name, direction=file_col.direction)
				elif isinstance(db_col, IntegerField):
					utils.write_int(file, name, direction=file_col.direction)
				elif isinstance(db_col, DoubleField):
					utils.write_num(file, name, direction=file_col.direction)
				elif isinstance(db_col, BooleanField):
					utils.write_code(file, name, direction=file_col.direction)
				else:
					utils.write_string(file, name, direction=file_col.direction)

	def write_row(self, file, cols):
		for file_col in cols:
			string_null = file_col.text_if_null if file_col.text_if_null is not None else utils.NULL_STR
			num_null = file_col.text_if_null if file_col.text_if_null is not None else utils.NULL_NUM

			if file_col.is_desc:
				utils.write_desc_string(file, file_col.value)
			elif file_col.padding_override is not None:
				if isinstance(file_col.value, int):
					utils.write_int(file, file_col.value, default_pad=file_col.padding_override, direction=file_col.direction)
				elif isinstance(file_col.value, float):
					utils.write_num(file, file_col.value, default_pad=file_col.padding_override, direction=file_col.direction, text_if_null=num_null, use_non_zero_min=file_col.use_non_zero_min)
				else:
					utils.write_string(file, file_col.value, default_pad=file_col.padding_override, direction=file_col.direction, text_if_null=string_null)
			elif isinstance(file_col.value, int):
				utils.write_int(file, file_col.value, direction=file_col.direction)
			elif isinstance(file_col.value, float):
				utils.write_num(file, file_col.value, direction=file_col.direction, text_if_null=num_null, use_non_zero_min=file_col.use_non_zero_min)
			elif isinstance(file_col.value, bool):
				utils.write_bool_yn(file, file_col.value, direction=file_col.direction, text_if_null=num_null)
			else:
				utils.write_string(file, file_col.value, direction=file_col.direction, text_if_null=string_null)

	def write_table(self, table, cols, write_cnt_line=False):
		self.write_query(table.select().order_by(table.id), cols, write_cnt_line)

	def write_default_table(self, table, ignore_id_col=False, ignored_cols=[], non_zero_min_cols=[], write_cnt_line=False):
		self.write_custom_query_table(table, table.select().order_by(table.id), ignore_id_col=ignore_id_col, ignored_cols=ignored_cols, non_zero_min_cols=non_zero_min_cols, write_cnt_line=write_cnt_line)

	def write_custom_query_table(self, table, query, ignore_id_col=False, ignored_cols=[], non_zero_min_cols=[], write_cnt_line=False):
		if table.select().count() > 0:
			cols = []
			for field in table._meta.sorted_fields:
				col = FileColumn(field)

				if field.name == "desc" or field.name == "description":
					col = FileColumn(field, is_desc=True)
				elif field.name == "name":
					col = FileColumn(field, direction="left")
				elif field.name in non_zero_min_cols:
					col = FileColumn(field, use_non_zero_min=True)

				if not ignore_id_col or field.name != "id":
					if field.name not in ignored_cols:
						cols.append(col)

			self.write_query(query, cols, write_cnt_line)

	def write_default_csv(self, table, ignore_id_col=False, ignored_cols=[]):
		write_csv(self.file_name, table, ignore_id_col, ignored_cols)

	def write_query(self, query, cols, write_cnt_line=False):
		if query.count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)

				if write_cnt_line:
					file.write(str(query.count()))
					file.write("\n")

				self.write_headers(file, cols)
				file.write("\n")

				i = 1
				for row in query.dicts():
					row_cols = []
					for col in cols:
						col_name = col.query_alias if col.query_alias != "" else col.value.name
						col_value = i if col_name == "id" else row[col_name]
						row_cols.append(FileColumn(col_value, direction=col.direction, padding_override=col.padding_override, text_if_null=col.text_if_null, is_desc=col.is_desc, use_non_zero_min=col.use_non_zero_min))

					self.write_row(file, row_cols)
					file.write("\n")
					i += 1

	def read_default_table(self, table, db, expected_cols, ignore_id_col=False, start_line=3, csv=False, convert_name_to_lower=False, overwrite=FileOverwrite.ignore):
		read_file(self.file_name, table, db, expected_cols, ignore_id_col, start_line, csv, convert_name_to_lower, overwrite)


	# keep still for smaller uses like aquifers and calibration
	def write_ele_ids(self, file, table, element_table, elements, use_obj_id=True):
		"""
		SWAT+ requires line numbers rather than designated ID numbers.
		The following writes the number of the element based on what line it will be in the ls_unit.ele file.
		The format of the element list uses a "-" to denote "through"
		"""
		last_id = 0
		last_appended_id = 0
		just_wrote = False
		ele_to_write = []
		for ele in elements.order_by(element_table.id):
			elem_table = table_mapper.obj_typs.get(ele.obj_typ, None)
			if elem_table is not None:
				if use_obj_id:
					obj_id_col = ele.obj_id
				else:
					obj_id_col = ele.obj_typ_no

				obj_id = elem_table.select().where(elem_table.id <= obj_id_col).count()
				if last_id == 0:
					ele_to_write.append(utils.int_pad(obj_id))
					just_wrote = True
					last_appended_id = obj_id
				elif obj_id > (last_id + 1):
					if last_appended_id != last_id:
						ele_to_write.append(utils.int_pad(last_id * -1))
					ele_to_write.append(utils.int_pad(obj_id))
					last_appended_id = obj_id
					just_wrote = True
				else:
					just_wrote = False
				last_id = obj_id

		if not just_wrote and len(elements) > 0:
			ele_to_write.append(utils.int_pad(last_id * -1))

		file.write(utils.int_pad(len(ele_to_write)))
		for w in ele_to_write:
			file.write(w)

	def write_ele_ids2(self, file, table, element_table, elements, elem_table, element_ids, use_obj_id=True):
		"""
		SWAT+ requires line numbers rather than designated ID numbers.
		The following writes the number of the element based on what line it will be in the ls_unit.ele file.
		The format of the element list uses a "-" to denote "through"
		"""
		last_id = 0
		last_appended_id = 0
		just_wrote = False
		ele_to_write = []
		for ele in elements.order_by(element_table.id):
			#elem_table = table_mapper.obj_typs.get(ele.obj_typ, None)
			if elem_table is not None:
				if use_obj_id:
					obj_id_col = ele.obj_id
				else:
					obj_id_col = ele.obj_typ_no

				#obj_id = elem_table.select().where(elem_table.id <= obj_id_col).count()
				obj_id = element_ids.index(obj_id_col) + 1
				if last_id == 0:
					ele_to_write.append(utils.int_pad(obj_id))
					just_wrote = True
					last_appended_id = obj_id
				elif obj_id > (last_id + 1):
					if last_appended_id != last_id:
						ele_to_write.append(utils.int_pad(last_id * -1))
					ele_to_write.append(utils.int_pad(obj_id))
					last_appended_id = obj_id
					just_wrote = True
				else:
					just_wrote = False
				last_id = obj_id

		if not just_wrote and len(elements) > 0:
			ele_to_write.append(utils.int_pad(last_id * -1))

		file.write(utils.int_pad(len(ele_to_write)))
		for w in ele_to_write:
			file.write(w)


class FileColumn:
	def __init__(self, value, direction="right", padding_override=None, not_in_db=False, repeat=None, alt_header_name="", query_alias="", text_if_null=None, is_desc=False, use_non_zero_min=False):
		self.value = value
		self.direction = direction
		self.padding_override = padding_override
		self.not_in_db = not_in_db
		self.repeat = repeat
		self.alt_header_name = alt_header_name
		self.query_alias = query_alias
		self.text_if_null = text_if_null
		self.is_desc = is_desc
		self.use_non_zero_min = use_non_zero_min
