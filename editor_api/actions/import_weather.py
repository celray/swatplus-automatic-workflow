from helpers.executable_api import ExecutableApi, Unbuffered
from database.project import base as project_base
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.project.climate import Weather_file, Weather_sta_cli, Weather_wgn_cli, Weather_wgn_cli_mon
from database.project.connect import Aquifer_con, Channel_con, Rout_unit_con, Reservoir_con, Recall_con, Hru_con, Exco_con, Chandeg_con, Hru_lte_con
from database.project.simulation import Time_sim
from database import lib as db_lib
from helpers import utils
from fileio import base as fileio

import sys
import os, os.path
import math
import argparse
import time, datetime
import sqlite3
from peewee import *


HMD_TXT = "hmd.txt"
PCP_TXT = "pcp.txt"
SLR_TXT = "slr.txt"
TMP_TXT = "tmp.txt"
WND_TXT = "wnd.txt"

HMD_TXT2 = "rh.txt"
SLR_TXT2 = "solar.txt"
WND_TXT2 = "wind.txt"

HMD_CLI = "hmd.cli"
PCP_CLI = "pcp.cli"
SLR_CLI = "slr.cli"
TMP_CLI = "tmp.cli"
WND_CLI = "wnd.cli"

WEATHER_DESC = {
	"hmd": "Relative humidity",
	"pcp": "Precipitation",
	"slr": "Solar radiation",
	"tmp": "Temperature",
	"wnd": "Wind speed"
}

def weather_sta_name(lat, lon, prefix = 's', mult = 1000):
	latp = "n" if lat >= 0 else "s"
	lonp = "e" if lon >= 0 else "w"
	name = "{prefix}{lat}{latp}{lon}{lonp}".format(prefix=prefix, lat=abs(round(lat * mult)), latp=latp, lon=abs(round(lon * mult)), lonp=lonp)
	return name


def update_closest_lat_lon(update_table, update_field, select_table, select_field="id", wtype=None):
	where = ""
	if wtype is not None:
		where = "where t2.type = ?"

	sql = """with r as
		(
			select t1.id as con_id, t2.{select_field} as wid, ((t1.lat - t2.lat) * (t1.lat - t2.lat) + (t1.lon - t2.lon) * (t1.lon - t2.lon)) as ord
			from {update_table} t1, {select_table} t2 {where}
			group by con_id
			having min(ord) or ord = 0
			order by con_id, ord
		)
		update {update_table} set {update_field} = (select wid from r where con_id = {update_table}.id)""".format(
			update_table=update_table, update_field=update_field, select_table=select_table, select_field=select_field, where=where)
	
	if wtype is not None:
		project_base.db.execute_sql(sql, (wtype,))
	else:
		project_base.db.execute_sql(sql)


def closest_lat_lon(db, table_name, lat, lon, wtype=None):
	"""
	See: http://stackoverflow.com/a/7472230
	For explanation of getting the closest lat,long
	"""
	#if not db_lib.exists_table(sqlite3.connect(db), table_name):
		#raise ValueError("Table {table} does not exist in {file}.".format(table=table_name, file=db))

	fudge = math.pow(math.cos(math.radians(lat)), 2)
	q = "order by ((? - lat) * (? - lat) + (? - lon) * (? - lon) * ?) limit 1"
	if wtype is None:
		cursor = project_base.db.execute_sql(
			"select id from {table} {q}".format(table=table_name, q=q),
			(lat, lat, lon, lon, fudge))
	else:
		cursor = project_base.db.execute_sql(
			"select filename from {table} where type = ? {q}".format(table=table_name, q=q),
			(wtype, lat, lat, lon, lon, fudge))
	res = cursor.fetchone()
	
	if res is None:
		return None
	
	return res[0]


class WeatherImport(ExecutableApi):
	def __init__(self, project_db_file, delete_existing, create_stations):
		self.__abort = False
		SetupProjectDatabase.init(project_db_file)
		self.project_db_file = project_db_file
		self.project_db = project_base.db
		self.create_stations = create_stations
		self.coords_to_stations = {}

		if delete_existing:
			self.delete_existing()

	def import_data(self):
		try:
			config = Project_config.get()
			
			weather_data_dir = utils.full_path(self.project_db_file, config.weather_data_dir)
			if not os.path.exists(weather_data_dir):
				sys.exit('Weather data directory {dir} does not exist.'.format(dir=weather_data_dir))

			self.add_weather_files(weather_data_dir)

			if self.create_stations:
				self.create_weather_stations(20, 45)
				self.match_stations(65)
			else:
				self.match_files_to_stations(20, 45)
		except Project_config.DoesNotExist:
			sys.exit('Could not retrieve project configuration from database')

	def delete_existing(self):
		Weather_file.delete().execute()
		Weather_sta_cli.delete().execute()

	def match_stations(self, start_prog):
		self.emit_progress(start_prog, "Adding weather stations to spatial connection tables...")
		wst_col = "wst_id"
		wst_table = "weather_sta_cli"
		update_closest_lat_lon("aquifer_con", wst_col, wst_table)
		update_closest_lat_lon("channel_con", wst_col, wst_table)
		update_closest_lat_lon("chandeg_con", wst_col, wst_table)
		update_closest_lat_lon("rout_unit_con", wst_col, wst_table)
		update_closest_lat_lon("reservoir_con", wst_col, wst_table)
		update_closest_lat_lon("recall_con", wst_col, wst_table)
		update_closest_lat_lon("exco_con", wst_col, wst_table)
		update_closest_lat_lon("hru_con", wst_col, wst_table)
		update_closest_lat_lon("hru_lte_con", wst_col, wst_table)
		update_closest_lat_lon("weather_sta_cli", "wgn_id", "weather_wgn_cli")

		"""self.match_stations_table(Aquifer_con, "aquifer connections", start_prog)
		self.match_stations_table(Channel_con, "channel connections", start_prog + 5)
		self.match_stations_table(Chandeg_con, "channel connections", start_prog + 5)
		self.match_stations_table(Rout_unit_con, "routing unit connections", start_prog + 10)
		self.match_stations_table(Reservoir_con, "reservoir connections", start_prog + 15)
		self.match_stations_table(Recall_con, "recall connections", start_prog + 20)
		self.match_stations_table(Exco_con, "exco connections", start_prog + 20)
		self.match_stations_table(Hru_con, "hru connections", start_prog + 25)
		self.match_stations_table(Hru_lte_con, "hru connections", start_prog + 25)
		self.match_wgn(start_prog + 30)"""

	def match_stations_table(self, table, name, prog):
		self.emit_progress(prog, "Adding weather stations to {name}...".format(name=name))
		with project_base.db.atomic():
			for row in table.select():
				coords_key = "{lat},{lon}".format(lat=row.lat, lon=row.lon)
				id = self.coords_to_stations.get(coords_key, None)
				if id is None:
					id = closest_lat_lon(project_base.db, "weather_sta_cli", row.lat, row.lon)
					self.coords_to_stations[coords_key] = id

				row.wst = id
				row.save()

	def match_wgn(self, prog):
		if Weather_wgn_cli.select().count() > 0:
			self.emit_progress(prog, "Matching wgn to weather stations...")
			with project_base.db.atomic():
				for row in Weather_sta_cli.select():
					id = closest_lat_lon(project_base.db, "weather_wgn_cli", row.lat, row.lon)
					row.wgn = id
					row.save()

	def create_weather_stations(self, start_prog, total_prog):  # total_prog is the total progress percentage available for this method
		if self.__abort: return

		stations = []
		cursor = project_base.db.execute_sql("select lat, lon from weather_file group by lat, lon")
		data = cursor.fetchall()
		records = len(data)
		i = 1
		for row in data:
			if self.__abort: return

			lat = row[0]
			lon = row[1]
			name = weather_sta_name(lat, lon)

			prog = round(i * total_prog / records) + start_prog
			self.emit_progress(prog, "Creating weather station {name}...".format(name=name))

			try:
				existing = Weather_sta_cli.get(Weather_sta_cli.name == name)
			except Weather_sta_cli.DoesNotExist:
				station = {
					"name": name,
					"wnd_dir": None,
					"atmo_dep": None,
					"lat": lat,
					"lon": lon,
					
				}

				"""
					"hmd": closest_lat_lon(project_base.db, "weather_file", lat, lon, "hmd"),
					"pcp": closest_lat_lon(project_base.db, "weather_file", lat, lon, "pcp"),
					"slr": closest_lat_lon(project_base.db, "weather_file", lat, lon, "slr"),
					"tmp": closest_lat_lon(project_base.db, "weather_file", lat, lon, "tmp"),
					"wnd": closest_lat_lon(project_base.db, "weather_file", lat, lon, "wnd")
					"""

				stations.append(station)
			i += 1

		db_lib.bulk_insert(project_base.db, Weather_sta_cli, stations)
		self.match_files_to_stations(45, 45)

	def match_files_to_stations(self, start_prog, total_prog):
		self.emit_progress(start_prog, "Matching files to weather station...")
		update_closest_lat_lon("weather_sta_cli", "hmd", "weather_file", "filename", "hmd")
		update_closest_lat_lon("weather_sta_cli", "pcp", "weather_file", "filename", "pcp")
		update_closest_lat_lon("weather_sta_cli", "slr", "weather_file", "filename", "slr")
		update_closest_lat_lon("weather_sta_cli", "tmp", "weather_file", "filename", "tmp")
		update_closest_lat_lon("weather_sta_cli", "wnd", "weather_file", "filename", "wnd")
		"""with project_base.db.atomic():
			query = Weather_sta_cli.select()
			records = query.count()
			i = 1
			for row in query:
				prog = round(i * total_prog / records) + start_prog
				self.emit_progress(prog, "Matching files to weather station {name}...".format(name=row.name))
				row.hmd = closest_lat_lon(project_base.db, "weather_file", row.lat, row.lon, "hmd")
				row.pcp = closest_lat_lon(project_base.db, "weather_file", row.lat, row.lon, "pcp")
				row.slr = closest_lat_lon(project_base.db, "weather_file", row.lat, row.lon, "slr")
				row.tmp = closest_lat_lon(project_base.db, "weather_file", row.lat, row.lon, "tmp")
				row.wnd = closest_lat_lon(project_base.db, "weather_file", row.lat, row.lon, "wnd")
				row.save()
				i += 1"""

	def add_weather_files(self, dir):
		if self.__abort: return
		hmd_start, hmd_end = self.add_weather_files_type(os.path.join(dir, HMD_CLI), "hmd", 0)
		if self.__abort: return
		pcp_start, pcp_end = self.add_weather_files_type(os.path.join(dir, PCP_CLI), "pcp", 5)
		if self.__abort: return
		slr_start, slr_end = self.add_weather_files_type(os.path.join(dir, SLR_CLI), "slr", 10)
		if self.__abort: return
		tmp_start, tmp_end = self.add_weather_files_type(os.path.join(dir, TMP_CLI), "tmp", 15)
		if self.__abort: return
		wnd_start, wnd_end = self.add_weather_files_type(os.path.join(dir, WND_CLI), "wnd", 20)

		starts = [hmd_start, pcp_start, slr_start, tmp_start, wnd_start]
		ends = [hmd_end, pcp_end, slr_end, tmp_end, wnd_end]
		starts = [v for v in starts if v is not None]
		ends = [v for v in ends if v is not None]
		if len(starts) > 0:
			"""ustarts = list(dict.fromkeys(starts))
			uends = list(dict.fromkeys(ends))
			if len(ustarts) > 1 or len(uends) > 1:
				raise ValueError("Dates in weather files do not match. Make sure all weather files have the same starting and ending dates.")
			"""
			start_date = max(starts)
			end_date = min(ends)
			st = start_date.timetuple()
			start_day = st.tm_yday if st.tm_yday > 1 else 0
			start_year = st.tm_year

			et = end_date.timetuple()
			end_day = 0 if et.tm_mon == 12 and et.tm_mday == 31 else et.tm_yday
			end_year = et.tm_year

			Time_sim.update(day_start=start_day, yrc_start=start_year, day_end=end_day, yrc_end=end_year).execute()

		if self.__abort: return
		"""warnings = []
		warnings.append(hmd_res)
		warnings.append(pcp_res)
		warnings.append(slr_res)
		warnings.append(tmp_res)
		warnings.append(wnd_res)
		has_warnings = any(x is not None for x in warnings)

		if has_warnings:
			with open(os.path.join( dir, "__warnings.txt"), 'w+') as warning_file:
				for w in warnings:
					if w is not None:
						warning_file.write(w)
						warning_file.write("\n")"""

	def add_weather_files_type(self, source_file, weather_type, prog):
		start_date = None
		end_date = None
		starts = []
		ends = []
		if os.path.exists(source_file):
			self.emit_progress(prog, "Inserting {type} files and coordinates...".format(type=weather_type))
			weather_files = []
			dir = os.path.dirname(source_file)
			with open(source_file, "r") as source_data:
				i = 0
				for line in source_data:
					if self.__abort:
						break

					if i > 1:
						station_name = line.strip('\n')
						station_file = os.path.join(dir, station_name)
						if not os.path.exists(station_file):
							raise IOError("File {file} not found. Weather data import aborted.".format(file=station_file))

						try:
							existing = Weather_file.get((Weather_file.filename == station_name) & (Weather_file.type == weather_type))
						except Weather_file.DoesNotExist:
							with open(station_file, "r") as station_data:
								j = 0
								for sline in station_data:
									if j == 2:
										station_info = sline.strip().split()
										if len(station_info) < 4:
											raise ValueError("Invalid value at line {ln} of {file}. Expecting nbyr, tstep, lat, long, elev values separated by a space.".format(ln=str(j + 1), file=station_file))

										lat = float(station_info[2])
										lon = float(station_info[3])

										file = {
											"filename": station_name,
											"type": weather_type,
											"lat": lat,
											"lon": lon
										}
										weather_files.append(file)
									elif j == 3:
										begin_data = sline.strip().split()
										if len(begin_data) < 3:
											raise ValueError("Invalid value at line {ln} of {file}. Expecting year, julian day, and weather value separated by a space.".format(ln=str(j + 1), file=station_file))

										date = datetime.datetime(int(begin_data[0]), 1, 1)
										current_start_date = date + datetime.timedelta(days=int(begin_data[1])-1)
										#if start_date is not None and current_start_date != start_date:
										#	raise ValueError("Start dates in weather files do not match. Make sure all weather files have the same starting and ending dates.")

										#start_date = current_start_date
										starts.append(current_start_date)
									elif j > 3:
										break

									j += 1

								non_empty_lines = [sline for sline in station_data if sline]
								last_line = non_empty_lines[len(non_empty_lines)-1].strip().split()
								date = datetime.datetime(int(last_line[0]), 1, 1)
								current_end_date = date + datetime.timedelta(days=int(last_line[1])-1)
								#if end_date is not None and current_end_date != end_date:
								#	raise ValueError("Ending dates in weather files do not match. Make sure all weather files have the same starting and ending dates.")

								#end_date = current_end_date
								ends.append(current_end_date)

					i += 1

			db_lib.bulk_insert(project_base.db, Weather_file, weather_files)
			if len(starts) > 0 and len(ends) > 0:
				start_date = max(starts)
				end_date = min(ends)
		return start_date, end_date


class Swat2012WeatherImport(ExecutableApi):
	def __init__(self, project_db_file, delete_existing, create_stations, source_dir):
		self.__abort = False
		SetupProjectDatabase.init(project_db_file)
		config = Project_config.get()
		
		weather_data_dir = utils.full_path(project_db_file, config.weather_data_dir)
		if not os.path.exists(weather_data_dir):
			sys.exit('Weather data directory {dir} does not exist.'.format(dir=weather_data_dir))

		self.output_dir = weather_data_dir
		self.project_db_file = project_db_file
		self.project_db = project_base.db
		self.source_dir = source_dir
		self.delete_existing = delete_existing
		self.create_stations = create_stations

	def import_data(self):
		try:
			self.write_to_swatplus(self.source_dir)
			weather_api = WeatherImport(self.project_db_file, self.delete_existing, self.create_stations)
			weather_api.import_data()
		except Project_config.DoesNotExist:
			sys.exit('Could not retrieve project configuration from database')

	def write_to_swatplus(self, dir):
		warnings = []

		if not os.path.exists(self.output_dir):
			os.makedirs(self.output_dir)

		total_files = len(os.listdir(dir))

		if self.__abort: return
		hmd_file = os.path.join(dir, HMD_TXT)
		if not os.path.exists(hmd_file):
			hmd_file = os.path.join(dir, HMD_TXT2)
		hmd_res = self.write_weather(hmd_file, os.path.join(self.output_dir, HMD_CLI), "hmd", 1, total_files)

		if self.__abort: return
		pcp_res = self.write_weather(os.path.join(dir, PCP_TXT), os.path.join(self.output_dir, PCP_CLI), "pcp", hmd_res[0], total_files)

		if self.__abort: return
		slr_file = os.path.join(dir, SLR_TXT)
		if not os.path.exists(slr_file):
			slr_file = os.path.join(dir, SLR_TXT2)
		slr_res = self.write_weather(slr_file, os.path.join(self.output_dir, SLR_CLI), "slr", pcp_res[0], total_files)

		if self.__abort: return
		tmp_res = self.write_weather(os.path.join(dir, TMP_TXT), os.path.join(self.output_dir, TMP_CLI), "tmp", slr_res[0], total_files)

		if self.__abort: return
		wnd_file = os.path.join(dir, WND_TXT)
		if not os.path.exists(wnd_file):
			wnd_file = os.path.join(dir, WND_TXT2)
		wnd_res = self.write_weather(wnd_file, os.path.join(self.output_dir, WND_CLI), "wnd", tmp_res[0], total_files)

		if self.__abort: return
		warnings.append(hmd_res[1])
		warnings.append(pcp_res[1])
		warnings.append(slr_res[1])
		warnings.append(tmp_res[1])
		warnings.append(wnd_res[1])
		has_warnings = any(x is not None for x in warnings)

		if has_warnings:
			with open(os.path.join(self.output_dir, "__warnings.txt"), 'w+') as warning_file:
				for w in warnings:
					if w is not None:
						warning_file.write(w)
						warning_file.write("\n")

	def write_weather(self, source_file, dest_file, weather_type, starting_file_num, total_files):
		if not os.path.exists(source_file):
			return starting_file_num, "Skipping {type} import. File does not exist: {file}".format(type=weather_type, file=source_file)
		else:
			with open(dest_file, 'w+') as new_file:
				new_file.write("{file}.cli: {desc} file names - file written by SWAT+ editor {today}\n".format(file=weather_type, desc=WEATHER_DESC[weather_type], today=datetime.datetime.now()))
				new_file.write("filename\n")
				new_file_names = []

				with open(source_file, "r") as source_data:
					i = 0
					curr_file_num = starting_file_num
					for line in source_data:
						if self.__abort:
							break

						if i == 0 and not "ID,NAME,LAT,LONG,ELEVATION" in line:
							return curr_file_num, "Skipping {type} import. Invalid file format in header: {file}. Expecting 'ID,NAME,LAT,LONG,ELEVATION'".format(type=weather_type, file=source_file)
						if i > 0:
							station_obj = [x.strip() for x in line.split(',')]
							if len(station_obj) != 5:
								return curr_file_num, "Skipping {type} import. Invalid file format in line {line_no}: {file}, {line}".format(type=weather_type, line_no=i+1, file=source_file, line=line)

							new_file_name = "{s}.{ext}".format(s=station_obj[1].replace("-", ""), ext=weather_type)
							new_file_names.append(new_file_name)
							#new_file.write(new_file_name)
							#new_file.write("\n")

							self.write_station(os.path.dirname(source_file), station_obj, weather_type)
							prog = round(curr_file_num * 100 / total_files)
							self.emit_progress(prog, "Writing {type}, {file}...".format(type=weather_type, file=new_file_name))
							curr_file_num += 1

						i += 1

				for fn in sorted(new_file_names, key=str.lower):
					new_file.write(fn)
					new_file.write("\n")

			return curr_file_num, None

	def write_station(self, dir, station_obj, weather_type):
		source_file = os.path.join(dir, "{s}.txt".format(s=station_obj[1]))
		if not os.path.exists(source_file):
			return "Skipping {type} import. Station file does not exist: {file}".format(type=weather_type, file=source_file)

		dest_file_name = "{s}.{ext}".format(s=station_obj[1].replace("-", ""), ext=weather_type)
		dest_file = os.path.join(self.output_dir, dest_file_name)

		with open(dest_file, 'w+') as new_file:
			new_file.write("{file}: {desc} data - file written by SWAT+ editor {today}\n".format(file=dest_file_name, desc=WEATHER_DESC[weather_type], today=datetime.datetime.now()))
			new_file.write("nbyr".rjust(4))
			new_file.write("tstep".rjust(10))
			new_file.write("lat".rjust(10))
			new_file.write("lon".rjust(10))
			new_file.write("elev".rjust(10))
			new_file.write("\n")

			linecount = self.file_len(source_file)
			total_days = linecount - 2 if linecount > 0 else 0

			with open(source_file, "r") as station_file:
				i = 0
				date = None
				for line in station_file:
					if i == 0:
						ts = time.strptime(line.strip(), "%Y%m%d")
						date = datetime.datetime(ts.tm_year, ts.tm_mon, ts.tm_mday)
						start_date = date

						end_date = start_date + datetime.timedelta(days=total_days)
						nbyr = end_date.year - start_date.year + 1

						new_file.write(str(nbyr).rjust(4))
						new_file.write("0".rjust(10))
						new_file.write("{0:.3f}".format(float(station_obj[2])).rjust(10))
						new_file.write("{0:.3f}".format(float(station_obj[3])).rjust(10))
						new_file.write("{0:.3f}".format(float(station_obj[4])).rjust(10))
						new_file.write("\n")
					else:
						day_of_year = date.timetuple().tm_yday

						new_file.write(str(date.year))
						new_file.write(str(day_of_year).rjust(5))
						new_file.write(' ')

						if weather_type == "tmp":
							tmp = [x.strip() for x in line.split(',')]
							utils.write_num(new_file, tmp[0], default_pad=10)
							utils.write_num(new_file, tmp[1], default_pad=10)
						else:
							utils.write_num(new_file, line, default_pad=10)
						new_file.write("\n")

						date = date + datetime.timedelta(days=1)

					i += 1

	def file_len(self, fname):
		with open(fname) as f:
			for i, l in enumerate(f):
				pass
		return i + 1


class WgnImport(ExecutableApi):
	def __init__(self, project_db_file, delete_existing, create_stations, import_method='database', file1=None, file2=None):
		self.__abort = False
		SetupProjectDatabase.init(project_db_file)
		self.project_db_file = project_db_file
		self.project_db = project_base.db
		self.create_stations = create_stations
		self.import_method = import_method
		self.file1 = file1
		self.file2 = file2

		try:
			config = Project_config.get()
			if self.import_method == 'database' and self.project_db_file != '' and self.project_db_file is not None:
				wgn_db = utils.full_path(self.project_db_file, config.wgn_db)
				if not os.path.exists(wgn_db):
					sys.exit('WGN path {dir} does not exist.'.format(dir=wgn_db))
					
				if config.wgn_table_name is None:
					sys.exit('Weather generator table name not set in config table.')

				self.wgn_database = wgn_db
				self.wgn_table = config.wgn_table_name
		except Project_config.DoesNotExist:
			sys.exit('Could not retrieve project configuration from database')

		if delete_existing:
			self.delete_existing()

	def import_data(self):
		if self.create_stations:
			self.add_wgn_stations(0, 50)
			self.create_weather_stations(50, 15)
			wi = WeatherImport(self.project_db_file, False, False)
			wi.match_stations(65)
		else:
			self.add_wgn_stations(0, 70)
			self.match_to_weather_stations(70, 30)

	def delete_existing(self):
		Weather_wgn_cli_mon.delete().execute()
		Weather_wgn_cli.delete().execute()

	def add_wgn_stations(self, start_prog, total_prog):
		if self.import_method == 'database':
			self.add_wgn_stations_db(start_prog, total_prog)
		elif self.import_method == 'two_file':
			self.add_wgn_stations_tf(start_prog, total_prog)
		elif self.import_method == 'one_file':
			self.add_wgn_stations_sf(start_prog, total_prog)
		else:
			sys.exit('Unsupported wgn import method.')

	def add_wgn_stations_tf(self, start_prog, total_prog):
		if self.__abort: return
		prog = (total_prog - start_prog) / 4 + start_prog
		self.emit_progress(prog, 'Adding weather generator stations...')
		fileio.read_csv_file(self.file1, Weather_wgn_cli, self.project_db, 0, ignore_id_col=False, overwrite=fileio.FileOverwrite.replace, remove_spaces_cols=['name'])
		prog = (total_prog - start_prog) / 2 + start_prog
		self.emit_progress(prog, 'Adding weather generator monthly values...')
		fileio.read_csv_file(self.file2, Weather_wgn_cli_mon, self.project_db, 0, ignore_id_col=False, overwrite=fileio.FileOverwrite.ignore)

	def add_wgn_stations_sf(self, start_prog, total_prog):
		if self.__abort: return

	def add_wgn_stations_db(self, start_prog, total_prog):
		if self.__abort: return
		conn = sqlite3.connect(self.wgn_database)
		conn.row_factory = sqlite3.Row

		monthly_table = "{}_mon".format(self.wgn_table)

		if not db_lib.exists_table(conn, self.wgn_table):
			raise ValueError(
				"Table {table} does not exist in {file}.".format(table=self.wgn_table, file=self.wgn_database))

		if not db_lib.exists_table(conn, monthly_table):
			raise ValueError(
				"Table {table} does not exist in {file}.".format(table=monthly_table, file=self.wgn_database))

		if Rout_unit_con.select().count() > 0:
			coords = Rout_unit_con.select(fn.Min(Rout_unit_con.lat).alias("min_lat"),
										  fn.Max(Rout_unit_con.lat).alias("max_lat"),
										  fn.Min(Rout_unit_con.lon).alias("min_lon"),
										  fn.Max(Rout_unit_con.lon).alias("max_lon")
										  ).get()

			query = "select * from {table_name} where lat between ? and ? and lon between ? and ? order by name".format(table_name=self.wgn_table)
			tol = 0.5
			cursor = conn.cursor().execute(query, (coords.min_lat - tol, coords.max_lat + tol, coords.min_lon - tol, coords.max_lon + tol))
		elif Chandeg_con.select().count() > 0:
			coords = Chandeg_con.select(fn.Min(Chandeg_con.lat).alias("min_lat"),
										  fn.Max(Chandeg_con.lat).alias("max_lat"),
										  fn.Min(Chandeg_con.lon).alias("min_lon"),
										  fn.Max(Chandeg_con.lon).alias("max_lon")
										  ).get()

			query = "select * from {table_name} where lat between ? and ? and lon between ? and ? order by name".format(table_name=self.wgn_table)
			tol = 0.5
			cursor = conn.cursor().execute(query, (coords.min_lat - tol, coords.max_lat + tol, coords.min_lon - tol, coords.max_lon + tol))
		else:
			query = "select * from {table_name} order by name".format(table_name=self.wgn_table)
			cursor = conn.cursor().execute(query)

		wgns = []
		ids = []

		data = cursor.fetchall()
		records = len(data)
		#print(records)

		i = 1
		for row in data:
			if self.__abort: return

			try:
				existing = Weather_wgn_cli.get(Weather_wgn_cli.name == row['name'])
			except Weather_wgn_cli.DoesNotExist:
				prog = round(i * (total_prog / 2) / records) + start_prog
				self.emit_progress(prog, "Preparing weather generator {name}...".format(name=row['name']))
				i += 1

				ids.append(row['id'])
				wgn = {
					"id": row['id'],
					"name": row['name'],
					"lat": row['lat'],
					"lon": row['lon'],
					"elev": row['elev'],
					"rain_yrs": row['rain_yrs']
				}
				wgns.append(wgn)

		prog = start_prog if records < 1 else round(i * (total_prog / 2) / records) + start_prog
		self.emit_progress(prog, "Inserting {total} weather generators...".format(total=len(ids)))
		db_lib.bulk_insert(project_base.db, Weather_wgn_cli, wgns)

		# Chunk the id array so we don't hit the SQLite parameter limit!
		max_length = 999
		id_chunks = [ids[i:i + max_length] for i in range(0, len(ids), max_length)]

		i = 1
		start_prog = start_prog + (total_prog / 2)

		mon_count_query = "select count(*) from {table_name}".format(table_name=monthly_table)
		total_mon_rows = conn.cursor().execute(mon_count_query).fetchone()[0]
		current_total = 0

		for chunk in id_chunks:
			monthly_values = []
			mon_query = "select * from {table_name} where wgn_id in ({ids})".format(table_name=monthly_table, ids=",".join('?'*len(chunk)))
			mon_cursor = conn.cursor().execute(mon_query, chunk)
			mon_data = mon_cursor.fetchall()
			mon_records = len(mon_data)
			i = 1

			for row in mon_data:
				if self.__abort: return

				if i == 1 or (i % 12 == 0):
					prog = round(i * (total_prog / 2) / mon_records) + start_prog
					self.emit_progress(prog, "Preparing monthly values {i}/{total}...".format(i=i, total=mon_records))
				i += 1

				mon = {
					"weather_wgn_cli": row['wgn_id'],
					"month": row['month'],
					"tmp_max_ave": row['tmp_max_ave'],
					"tmp_min_ave": row['tmp_min_ave'],
					"tmp_max_sd": row['tmp_max_sd'],
					"tmp_min_sd": row['tmp_min_sd'],
					"pcp_ave": row['pcp_ave'],
					"pcp_sd": row['pcp_sd'],
					"pcp_skew": row['pcp_skew'],
					"wet_dry": row['wet_dry'],
					"wet_wet": row['wet_wet'],
					"pcp_days": row['pcp_days'],
					"pcp_hhr": row['pcp_hhr'],
					"slr_ave": row['slr_ave'],
					"dew_ave": row['dew_ave'],
					"wnd_ave": row['wnd_ave']
				}
				monthly_values.append(mon)

			prog = round(i * (total_prog / 2) / mon_records) + start_prog
			current_total = current_total + mon_records
			self.emit_progress(prog, "Inserting monthly values {rec}/{total}...".format(rec=current_total, total=total_mon_rows))
			db_lib.bulk_insert(project_base.db, Weather_wgn_cli_mon, monthly_values)

	def create_weather_stations(self, start_prog, total_prog):  # total_prog is the total progress percentage available for this method
		if self.__abort: return

		stations = []
		query = Weather_wgn_cli.select()
		records = query.count()
		i = 1
		for row in query:
			if self.__abort: return

			lat = row.lat
			lon = row.lon
			#name = "w{lat}{lon}".format(lat=abs(round(lat*1000)), lon=abs(round(lon*1000)))
			name = weather_sta_name(lat, lon)

			prog = round(i * total_prog / records) + start_prog
			self.emit_progress(prog, "Creating weather station {name}...".format(name=name))

			try:
				existing = Weather_sta_cli.get(Weather_sta_cli.name == name)
			except Weather_sta_cli.DoesNotExist:
				station = {
					"name": name,
					"hmd": None,
					"pcp": None,
					"slr": None,
					"tmp": None,
					"wnd": None,
					"wnd_dir": None,
					"atmo_dep": None,
					"lat": lat,
					"lon": lon,
					"wgn": row.id
				}

				stations.append(station)
			i += 1

		db_lib.bulk_insert(project_base.db, Weather_sta_cli, stations)

	def match_to_weather_stations(self, start_prog, total_prog):
		if Weather_wgn_cli.select().count() > 0:
			with project_base.db.atomic():
				query = Weather_sta_cli.select()
				records = query.count()
				i = 1
				for row in query:
					if self.__abort: return

					prog = round(i * total_prog / records) + start_prog
					i += 1

					if row.lat is not None and row.lon is not None:
						id = closest_lat_lon(project_base.db, "weather_wgn_cli", row.lat, row.lon)

						self.emit_progress(prog, "Updating weather station with generator {i}/{total}...".format(i=i, total=records))
						row.wgn_id = id
						row.save()


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Import weather generator data into project SQLite database.")
	parser.add_argument("import_type", type=str, help="type of weather to import: observed, observed2012, wgn")
	parser.add_argument("project_db_file", type=str, help="full path of project SQLite database file")
	parser.add_argument("delete_existing", type=str, help="y/n delete existing data first")
	parser.add_argument("create_stations", type=str, help="y/n create stations for wgn")
	parser.add_argument("source_dir", type=str, help="full path of SWAT2012 weather files", nargs="?")
	args = parser.parse_args()

	del_ex = True if args.delete_existing == "y" else False
	cre_sta = True if args.create_stations == "y" else False

	if args.import_type == "observed":
		api = WeatherImport(args.project_db_file, del_ex, cre_sta)
		api.import_data()
	elif args.import_type == "observed2012":
		api = Swat2012WeatherImport(args.project_db_file, del_ex, cre_sta, args.source_dir)
		api.import_data()
	elif args.import_type == "wgn":
		api = WgnImport(args.project_db_file, del_ex, cre_sta)
		api.import_data()
