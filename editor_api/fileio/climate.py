from .base import BaseFileModel, FileColumn as col
from peewee import *
import database.project.climate as db


class Weather_sta_cli(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		table = db.Weather_sta_cli
		
		query = (table.select(table.name,
							  db.Weather_wgn_cli.name.alias("wgn"),
							  table.pcp,
							  table.tmp,
							  table.slr,
							  table.hmd,
							  table.wnd,
							  table.wnd_dir,
							  table.atmo_dep)
					  .join(db.Weather_wgn_cli, JOIN.LEFT_OUTER)
					  .order_by(table.name))

		cols = [col(table.name, direction="left"),
				col(table.wgn, query_alias="wgn"),
				col(table.pcp, padding_override=25, text_if_null="sim"),
				col(table.tmp, padding_override=25, text_if_null="sim"),
				col(table.slr, padding_override=25, text_if_null="sim"),
				col(table.hmd, padding_override=25, text_if_null="sim"),
				col(table.wnd, padding_override=25, text_if_null="sim"),
				col(table.wnd_dir, text_if_null="null"),
				col(table.atmo_dep, text_if_null="null")]
		self.write_query(query, cols)


class Weather_wgn_cli(BaseFileModel):
	def __init__(self, file_name, version=None, swat_version=None):
		self.file_name = file_name
		self.version = version
		self.swat_version = swat_version

	def read(self):
		raise NotImplementedError('Reading not implemented yet.')

	def write(self):
		wgn = db.Weather_wgn_cli.select().order_by(db.Weather_wgn_cli.name)
		months = db.Weather_wgn_cli_mon.select().order_by(db.Weather_wgn_cli_mon.month)
		query = prefetch(wgn, months)

		if wgn.count() > 0:
			with open(self.file_name, 'w') as file:
				self.write_meta_line(file)

				for row in query:
					row_cols = [col(row.name, direction="left", padding_override=25),
								col(row.lat),
								col(row.lon),
								col(row.elev),
								col(row.rain_yrs)]
					self.write_row(file, row_cols)
					file.write("\n")

					mt = db.Weather_wgn_cli_mon
					mon_cols = [col(mt.tmp_max_ave),
								col(mt.tmp_min_ave),
								col(mt.tmp_max_sd),
								col(mt.tmp_min_sd),
								col(mt.pcp_ave),
								col(mt.pcp_sd),
								col(mt.pcp_skew),
								col(mt.wet_dry),
								col(mt.wet_wet),
								col(mt.pcp_days),
								col(mt.pcp_hhr),
								col(mt.slr_ave),
								col(mt.dew_ave),
								col(mt.wnd_ave)]
					self.write_headers(file, mon_cols)
					file.write("\n")

					for month in row.monthly_values:
						month_row_cols = [col(month.tmp_max_ave),
										  col(month.tmp_min_ave),
										  col(month.tmp_max_sd),
										  col(month.tmp_min_sd),
										  col(month.pcp_ave),
										  col(month.pcp_sd),
										  col(month.pcp_skew),
										  col(month.wet_dry),
										  col(month.wet_wet),
										  col(month.pcp_days),
										  col(month.pcp_hhr),
										  col(month.slr_ave),
										  col(month.dew_ave),
										  col(month.wnd_ave)]
						self.write_row(file, month_row_cols)
						file.write("\n")
