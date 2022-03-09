from .base import BaseFileModel, FileColumn as col
from helpers import utils
import database.project.decision_table as db
import database.datasets.decision_table as db_datasets

from database.project import base as project_base
from database.datasets import base as datasets_base
from database import lib as db_lib
from pathlib import Path


class D_table_dtl(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None, file_type=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version
		self.file_name_only = Path(file_name).name if file_type is None else file_type

	def set_tables(self, database ='project'):
		self.db_file = datasets_base.db
		self.d_table_dtl = db_datasets.D_table_dtl
		self.d_table_dtl_cond = db_datasets.D_table_dtl_cond
		self.d_table_dtl_cond_alt = db_datasets.D_table_dtl_cond_alt
		self.d_table_dtl_act = db_datasets.D_table_dtl_act
		self.d_table_dtl_act_out = db_datasets.D_table_dtl_act_out

		if database == 'project':
			self.db_file = project_base.db
			self.d_table_dtl = db.D_table_dtl
			self.d_table_dtl_cond = db.D_table_dtl_cond
			self.d_table_dtl_cond_alt = db.D_table_dtl_cond_alt
			self.d_table_dtl_act = db.D_table_dtl_act
			self.d_table_dtl_act_out = db.D_table_dtl_act_out

	def read(self, database ='project'):
		"""
		Read a d_table.dtl text file into the database.
		:param database: project or datasets
		:return:
		"""
		self.set_tables(database)

		file = open(self.file_name, "r")
		lines = file.readlines()

		i = 3
		while i < len(lines):
			while i < len(lines) and (lines[i] is None or lines[i].strip() == ''):
				i += 1

			if i < len(lines):
				i, new_table = self.read_table(lines, i)

	def read_table(self, lines, start_line, edit_id=None):
		i = start_line + 1  # Skip header

		#Try and get table description
		table_description = None
		header_vals = lines[start_line].strip().split('!')
		if len(header_vals) > 1:
			table_description = header_vals[1]

		vals = lines[i].strip().split()
		self.check_cols(vals, 4, 'decision table')
		table_name = vals[0].strip()
		num_conds = int(vals[1])
		num_alts = int(vals[2])
		num_acts = int(vals[3])

		do_del_existing = edit_id is not None
		if edit_id is None:
			table, created = self.d_table_dtl.get_or_create(name=table_name, file_name=self.file_name_only)
			if not created:
				do_del_existing = True

			if table_description is not None:
				table.description = table_description
				table.save()
		else:
			table = self.d_table_dtl.get_or_none(self.d_table_dtl.id == edit_id)

		if do_del_existing:
			cond_ids = self.d_table_dtl_cond.select(self.d_table_dtl_cond.id).where(self.d_table_dtl_cond.d_table_id == table.id)
			act_ids = self.d_table_dtl_act.select(self.d_table_dtl_act.id).where(self.d_table_dtl_act.d_table_id == table.id)
			self.d_table_dtl_cond_alt.delete().where(self.d_table_dtl_cond_alt.cond_id.in_(cond_ids)).execute()
			self.d_table_dtl_act_out.delete().where(self.d_table_dtl_act_out.act_id.in_(act_ids)).execute()

			self.d_table_dtl_cond.delete().where(self.d_table_dtl_cond.d_table_id == table.id).execute()
			self.d_table_dtl_act.delete().where(self.d_table_dtl_act.d_table_id == table.id).execute()

		i += 2  # Skip header
		cond_cols = 6
		max_cond_lines = i + num_conds
		while i < max_cond_lines:
			cond_vals = lines[i].strip().split()
			self.check_cols(cond_vals, cond_cols + num_alts, 'decision table condition line {}'.format(i))

			cond_description = None
			cond_header_vals = lines[i].strip().split('!')
			if len(cond_header_vals) > 1:
				cond_description = cond_header_vals[1]

			cond = self.d_table_dtl_cond()
			cond.d_table = table
			cond.var = cond_vals[0]
			cond.obj = cond_vals[1]
			cond.obj_num = int(cond_vals[2])
			cond.lim_var = cond_vals[3]
			cond.lim_op = cond_vals[4]
			cond.lim_const = float(cond_vals[5])
			cond.description = cond_description
			cond.save()

			for j in range(0, num_alts):
				alt = self.d_table_dtl_cond_alt()
				alt.cond = cond
				alt.alt = cond_vals[j + cond_cols]
				alt.save()

			i += 1

		i += 1  # Skip header
		act_cols = 8
		max_act_lines = i + num_acts
		while i < max_act_lines:
			act_vals = lines[i].strip().split()
			self.check_cols(act_vals, act_cols, 'decision table actions')

			act = self.d_table_dtl_act()
			act.d_table = table
			act.act_typ = act_vals[0]
			act.obj = act_vals[1]
			act.obj_num = int(act_vals[2])
			act.name = act_vals[3]
			act.option = act_vals[4]
			act.const = act_vals[5]
			act.const2 = act_vals[6]
			act.fp = act_vals[7]
			act.save()

			for k in range(act_cols, len(act_vals)):
				outcome = self.d_table_dtl_act_out()
				outcome.act = act
				outcome.outcome = act_vals[k].strip() == 'y'
				outcome.save()

			i += 1

		i += 1
		return i, table

	def write(self):
		d_tables = db.D_table_dtl.select().where(db.D_table_dtl.file_name == self.file_name_only).order_by(db.D_table_dtl.id)

		if d_tables.count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)
				file.write("{}".format(d_tables.count()))
				file.write("\n")
				file.write("\n")

				for d_table in d_tables:
					table_header_cols = [col(db.D_table_dtl.name, direction="left", padding_override=20),
										 col("conds", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
										 col("alts", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD),
										 col("acts", not_in_db=True, padding_override=utils.DEFAULT_INT_PAD)]
					self.write_headers(file, table_header_cols)
					if d_table.description is not None:
						file.write("     !{}".format(d_table.description))
					file.write("\n")

					first_cond = d_table.conditions.first()
					num_alts = first_cond.alts.count()

					d_table_cols = [col(d_table.name, direction="left", padding_override=20),
									col(d_table.conditions.count()),
									col(num_alts),
									col(d_table.actions.count())]
					self.write_row(file, d_table_cols)
					file.write("\n")

					cond_header_cols = [col(db.D_table_dtl_cond.var, direction="left", padding_override=20),
										col(db.D_table_dtl_cond.obj, padding_override=utils.DEFAULT_INT_PAD),
										col(db.D_table_dtl_cond.obj_num),
										col(db.D_table_dtl_cond.lim_var),
										col(db.D_table_dtl_cond.lim_op),
										col(db.D_table_dtl_cond.lim_const)]

					for i in range(0, num_alts):
						cond_header_cols.append(col("alt{}".format(i+1), not_in_db=True, padding_override=utils.DEFAULT_INT_PAD))

					self.write_headers(file, cond_header_cols)
					file.write("\n")

					for cond in d_table.conditions:
						cond_cols = [col(cond.var, direction="left", padding_override=20),
									 col(cond.obj, padding_override=utils.DEFAULT_INT_PAD),
									 col(cond.obj_num),
									 col(cond.lim_var),
									 col(cond.lim_op),
									 col(cond.lim_const)]

						for alt in cond.alts:
							cond_cols.append(col(alt.alt, padding_override=utils.DEFAULT_INT_PAD))

						self.write_row(file, cond_cols)
						if cond.description is not None:
							file.write("     !{}".format(cond.description))
						file.write("\n")

					act_header_cols = [col(db.D_table_dtl_act.act_typ, direction="left", padding_override=20),
									   col(db.D_table_dtl_act.obj, padding_override=utils.DEFAULT_INT_PAD),
									   col(db.D_table_dtl_act.obj_num),
									   col(db.D_table_dtl_act.name),
									   col(db.D_table_dtl_act.option),
									   col(db.D_table_dtl_act.const),
									   col(db.D_table_dtl_act.const2),
									   col(db.D_table_dtl_act.fp),
									   col("outcome", not_in_db=True, direction="left", padding_override=utils.DEFAULT_STR_PAD)]

					self.write_headers(file, act_header_cols)
					file.write("\n")

					for act in d_table.actions:
						act_cols = [col(act.act_typ, direction="left", padding_override=20),
									col(act.obj, padding_override=utils.DEFAULT_INT_PAD),
									col(act.obj_num),
									col(act.name),
									col(act.option),
									col(act.const),
									col(act.const2),
									col(act.fp)]

						for outcome in act.outcomes:
							str_val = "y" if outcome.outcome else "n"
							act_cols.append(col(str_val, direction="left", padding_override=2))

						self.write_row(file, act_cols)
						file.write("\n")

					file.write("\n")
