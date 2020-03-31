from .base import BaseFileModel, FileColumn as col
from peewee import *
from helpers import utils
import database.project.lum as db
import database.datasets.lum as db_datasets

from database.project.decision_table import D_table_dtl as project_d_table
from database.datasets.decision_table import D_table_dtl as datasets_d_table

from database.project import base as project_base
from database.datasets import base as datasets_base
from database import lib as db_lib


class Management_sch(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		"""
		Read a management.sch text file into the database.
		:param database: project or datasets
		:return:
		"""
		self.db_file = datasets_base.db
		self.d_table_dtl = datasets_d_table
		self.mgt_sch = db_datasets.Management_sch
		self.mgt_sch_op = db_datasets.Management_sch_op
		self.mgt_sch_auto = db_datasets.Management_sch_auto
		
		if database == 'project':
			self.db_file = project_base.db
			self.d_table_dtl = project_d_table
			self.mgt_sch = db.Management_sch
			self.mgt_sch_op = db.Management_sch_op
			self.mgt_sch_auto = db.Management_sch_auto
		
		file = open(self.file_name, "r")
		lines = file.readlines()
		
		i = 2
		while i < len(lines):
			while i < len(lines) and (lines[i] is None or lines[i].strip() == ''):
				i += 1
			
			if i < len(lines):
				i = self.read_table(lines, i)
			
	def read_table(self, lines, start_line):
		i = start_line
		vals = lines[i].split()
		self.check_cols(vals, 3, 'management schedule {i}'.format(i=i))
		name = vals[0].strip()
		num_ops = int(vals[1])
		num_auto = int(vals[2])

		sch, created = self.mgt_sch.get_or_create(name=name)

		if not created:
			self.mgt_sch_auto.delete().where(self.mgt_sch_auto.management_sch_id == sch.id).execute()
			self.mgt_sch_op.delete().where(self.mgt_sch_op.management_sch_id == sch.id).execute()

		i += 1  # Next line
		max_auto_lines = i + num_auto
		while i < max_auto_lines:
			mgt_auto_name = lines[i].strip()
			try:
				d = self.d_table_dtl.get(self.d_table_dtl.name == mgt_auto_name)
				
				self.mgt_sch_auto.create(
					management_sch=sch.id,
					d_table=d.id
				)
			except self.d_table_dtl.DoesNotExist:
				raise ValueError('Decision table {name} does not exist.'.format(name=mgt_auto_name))
			i += 1
			
		max_op_lines = i + num_ops
		o = 1
		while i < max_op_lines:
			vals = lines[i].split()
			self.check_cols(vals, 7, 'management schedule operation')
			
			description = None
			if len(vals) > 7:
				description = ' '.join(vals[7:])
			
			self.mgt_sch_op.create(
				management_sch=sch.id,
				op_typ=vals[0].strip(),
				mon=int(vals[1]),
				day=int(vals[2]),
				hu_sch=float(vals[3]),
				op_data1=vals[4].strip() if vals[4].strip() != 'null' else None,
				op_data2=vals[5].strip() if vals[5].strip() != 'null' else None,
				op_data3=float(vals[6]),
				description=description,
				order=o
			)
			i += 1
			o += 1
			
		return i

	def write(self):
		table = db.Management_sch
		op_table = db.Management_sch_op

		mgts = table.select().order_by(table.id)
		ops = op_table.select().order_by(op_table.order, op_table.hu_sch, op_table.mon, op_table.day)
		query = prefetch(mgts, ops)

		if mgts.count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				header_cols = [col(table.name, direction="left", padding_override=25),
							   col("numb_ops", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
							   col("numb_auto", not_in_db=True, padding_override=9),
							   col(op_table.op_typ),
							   col(op_table.mon),
							   col(op_table.day),
							   col(op_table.hu_sch),
							   col(op_table.op_data1),
							   col(op_table.op_data2),
							   col(op_table.op_data3)]
				self.write_headers(file, header_cols)

				total_pad = 46

				file.write("\n")

				for row in query:
					row_cols = [col(row.name, direction="left", padding_override=25),
								col(len(row.operations)),
								col(len(row.auto_ops), padding_override=9)]
					self.write_row(file, row_cols)
					file.write("\n")
					
					for aop in row.auto_ops:
						file.write(utils.string_pad(" ", default_pad=total_pad))
						file.write(utils.key_name_pad(aop.d_table))
						file.write("\n")

					skip_op = 'skip'

					for op in row.operations:
						op_row_cols = [col(" ", padding_override=total_pad),
									   col(op.op_typ),
									   col(op.mon if op.op_typ != skip_op else 0),
									   col(op.day if op.op_typ != skip_op else 0),
									   col(op.hu_sch if op.op_typ != skip_op else 0),
									   col(op.op_data1),
									   col(op.op_data2),
									   col(op.op_data3)]
						self.write_row(file, op_row_cols)
						file.write("\n")


class Landuse_lum(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Landuse_lum
		order_by = db.Landuse_lum.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.name, padding_override=20, direction="left"),
						col(table.cal_group),
						col(table.plnt_com),
						col(table.mgt),
						col(table.cn2),
						col(table.cons_prac),
						col(table.urban),
						col(table.urb_ro),
						col(table.ov_mann),
						col(table.tile),
						col(table.sep),
						col(table.vfs),
						col(table.grww),
						col(table.bmp)]
				self.write_headers(file, cols)
				file.write("\n")

				for row in table.select().order_by(order_by):
					file.write(utils.string_pad(row.name, direction="left", default_pad=20))
					file.write(utils.string_pad(row.cal_group))
					file.write(utils.key_name_pad(row.plnt_com))
					file.write(utils.key_name_pad(row.mgt))
					file.write(utils.key_name_pad(row.cn2))
					file.write(utils.key_name_pad(row.cons_prac))
					file.write(utils.key_name_pad(row.urban))
					file.write(utils.string_pad(row.urb_ro))
					file.write(utils.key_name_pad(row.ov_mann))
					file.write(utils.key_name_pad(row.tile))
					file.write(utils.key_name_pad(row.sep))
					file.write(utils.key_name_pad(row.vfs))
					file.write(utils.key_name_pad(row.grww))
					file.write(utils.key_name_pad(row.bmp))
					file.write("\n")


class Cntable_lum(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		"""
		Read a cntable.lum text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		cns = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 8, 'cntable.lum')

				cn = {
					'name': val[0].lower(),
					'cn_a': val[1],
					'cn_b': val[2],
					'cn_c': val[3],
					'cn_d': val[4],
					'description': val[5],
					'treat': val[6],
					'cond_cov': val[7]
				}
				cns.append(cn)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Cntable_lum, cns)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Cntable_lum, cns)

	def write(self):
		table = db.Cntable_lum
		order_by = db.Cntable_lum.id

		if table.select().count() > 0:
			with open(self.file_name, 'w') as file:
				file.write(self.get_meta_line())
				cols = [col(table.name, direction="left"),
						col(table.cn_a),
						col(table.cn_b),
						col(table.cn_c),
						col(table.cn_d),
						col(table.description, direction="left", padding_override=70),
						col(table.treat, direction="left", padding_override=40),
						col(table.cond_cov, direction="left")]
				self.write_headers(file, cols)
				file.write("\n")

				for row in table.select().order_by(order_by):
					cols = [col(row.name, direction="left"),
							col(row.cn_a),
							col(row.cn_b),
							col(row.cn_c),
							col(row.cn_d),
							col(row.description, direction="left", padding_override=70),
							col(row.treat, direction="left", padding_override=40),
							col(row.cond_cov, direction="left")]
					self.write_row(file, cols)
					file.write("\n")


class Ovn_table_lum(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		"""
		Read a ovn_table.lum text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 5, 'ovn_table.lum')

				d = {
					'name': val[0].lower(),
					'ovn_mean': val[1],
					'ovn_min': val[2],
					'ovn_max': val[3],
					'description': val[4]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Ovn_table_lum, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Ovn_table_lum, data)

	def write(self):
		self.write_default_table(db.Ovn_table_lum, True)


class Cons_prac_lum(BaseFileModel):
	def __init__(self, file_name, version=None):
		self.file_name = file_name
		self.version = version

	def read(self, database ='project'):
		"""
		Read a cons_practice.lum text file into the database.
		:param database: project or datasets
		:return:
		"""
		file = open(self.file_name, "r")

		i = 1
		data = []
		for line in file:
			if i > 2:
				val = line.split()
				self.check_cols(val, 4, 'cons_practice.lum')

				d = {
					'name': val[0].lower(),
					'usle_p': val[1],
					'slp_len_max': val[2],
					'description': val[3]
				}
				data.append(d)
			i += 1

		if database == 'project':
			db_lib.bulk_insert(project_base.db, db.Cons_prac_lum, data)
		else:
			db_lib.bulk_insert(datasets_base.db, db_datasets.Cons_prac_lum, data)

	def write(self):
		self.write_default_table(db.Cons_prac_lum, True)
