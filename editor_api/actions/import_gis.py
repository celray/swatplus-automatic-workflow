from helpers.executable_api import ExecutableApi, Unbuffered
from database import lib as db_lib
from database.project import base as project_base, gis, routing_unit, channel, connect, aquifer, hydrology, hru, \
	reservoir, soils, init, lum, hru_parm_db, exco, regions, recall, decision_table, climate
from database.project.setup import SetupProjectDatabase
from database.project.config import Project_config
from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import init as ds_init, lum as ds_lum, base as ds_base, hru_parm_db as ds_hru_parm_db
from database.datasets import definitions
from helpers import utils
from .import_weather import WeatherImport

from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.migrate import *

import sys
import argparse
import math

support_gis_versions = [
	'1.3',
	'1.2',
	'1.1',
	'1.0',
	'0.9',
	'0.8',
	'0.7',
	'0'
]


def is_supported_version(version):
	ver = version
	if len(ver) >= 3:
		ver = version[:3]
	if ver not in support_gis_versions:
		return False
	return True

def get_name(name, id, digits):
	return "{name}{num}".format(name=name, num=str(id).zfill(len(str(digits))))

def get_max_id(table):
	return table.select(fn.Max(table.id)).scalar()


class RouteCat:
	LSU = "LSU"
	PT = "PT"
	CH = "CH"
	WTR = "WTR"
	SUB = "SUB"
	HRU = "HRU"
	OUTLET = "X"
	RES = "RES"
	PND = "PND"
	WaterTypes = [WTR, RES, PND]


class GisImport(ExecutableApi):
	def __init__(self, project_db_file, delete_existing=False, constant_ps=True, rollback_db=None):
		SetupProjectDatabase.init(project_db_file)
		self.project_db_file = project_db_file
		self.project_db = project_base.db
		self.config = None,
		self.constant_ps = constant_ps
		self.rollback_db = rollback_db

		try:
			self.config = Project_config.get()
			self.is_lte = self.config.is_lte

			datasets_db = utils.full_path(project_db_file, self.config.reference_db)

			SetupDatasetsDatabase.init(datasets_db)
			self.reference_db = ds_base.db
			self.reference_db_file = datasets_db
		except Project_config.DoesNotExist:
			sys.exit("Could not retrieve project configuration data.")

		self.gis_to_rtu_ids = {}
		self.gis_to_cha_ids = {}
		self.gis_to_res_ids = {}
		self.gis_to_hru_ids = {}
		self.gis_to_flood_aqu_ids = {}
		self.gis_to_upland_aqu_ids = {}
		self.aqu_id_to_sub = {}
		self.sub_to_flood_aqu_id = {}
		self.sub_to_upland_aqu_id = {}

		if delete_existing and not self.config.imported_gis:
			self.delete_existing()

	def insert_default(self):
		if not self.config.imported_gis:
			try:
				if gis.Gis_subbasins.select().count() > 0:
					if not is_supported_version(self.config.gis_version):
						raise ValueError("This version of SWAT+ Editor does not support QSWAT+ {uv}.".format(uv=self.config.gis_version))
					
					self.emit_progress(5, "Checking for plants_plt updates...")
					self.update_plants()

					if self.is_lte:
						self.emit_progress(15, "Importing channels from GIS...")
						self.insert_om_water()
						self.insert_channels_lte()

						self.emit_progress(50, "Importing hrus from GIS...")
						self.insert_hru_ltes()

						self.emit_progress(90, "Importing connections from GIS...")
						self.insert_connections_lte()
					else:
						self.emit_progress(12, "Checking GIS water table...")
						self.update_gis_water()

						self.emit_progress(15, "Importing routing units from GIS...")
						self.insert_routing_units()

						self.emit_progress(30, "Importing channels from GIS...")
						self.insert_om_water()
						self.insert_channels_lte()

						self.emit_progress(40, "Importing reservoirs from GIS...")
						self.insert_reservoirs()

						self.emit_progress(50, "Importing point source from GIS...")
						self.insert_recall(is_lte_cha_type=True)

						self.emit_progress(60, "Importing hrus from GIS...")
						self.insert_hrus()
						
						self.emit_progress(75, "Creating aquifers...")
						self.insert_aquifers()

						self.emit_progress(90, "Importing connections from GIS...")
						self.insert_connections(is_lte_cha_type=True)

						self.emit_progress(95, "Creating default landscape units...              ")
						self.insert_lsus()

						if climate.Weather_sta_cli.select().count() > 0:
							w_api = WeatherImport(self.project_db_file, False, False)
							w_api.match_stations(70)

					config = Project_config.get()
					config.imported_gis = True
					config.save()
				else:
					self.emit_progress(95, "No GIS data to import...")
			except ValueError as err:
				if self.rollback_db is not None:
					self.emit_progress(50, "Error occurred. Rolling back database...")
					SetupProjectDatabase.rollback(self.project_db_file, self.rollback_db)
					self.emit_progress(100, "Error occurred.")
				sys.exit(err)

	def delete_existing(self):
		self.emit_progress(5, "Deleting existing connections before importing from GIS...")
		hydrology.Topography_hyd.delete().execute()
		hydrology.Hydrology_hyd.delete().execute()
		hydrology.Field_fld.delete().execute()
		
		init.Om_water_ini.delete().execute()
		init.Soil_plant_ini.delete().execute()

		channel.Hydrology_cha.delete().execute()
		channel.Sediment_cha.delete().execute()
		channel.Nutrients_cha.delete().execute()
		channel.Hyd_sed_lte_cha.delete().execute()
		channel.Initial_cha.delete().execute()
		channel.Channel_cha.delete().execute()
		channel.Channel_lte_cha.delete().execute()
		
		aquifer.Aquifer_aqu.delete().execute()
		aquifer.Initial_aqu.delete().execute()
		
		reservoir.Reservoir_res.delete().execute()
		reservoir.Initial_res.delete().execute()
		reservoir.Hydrology_res.delete().execute()
		reservoir.Nutrients_res.delete().execute()
		reservoir.Sediment_res.delete().execute()
		reservoir.Weir_res.delete().execute()
		reservoir.Hydrology_wet.delete().execute()
		reservoir.Wetland_wet.delete().execute()
		
		exco.Exco_exc.delete().execute()
		exco.Exco_om_exc.delete().execute()
		
		recall.Recall_rec.delete().execute()
		recall.Recall_dat.delete().execute()

		routing_unit.Rout_unit_rtu.delete().execute()
		connect.Rout_unit_ele.delete().execute()
		
		hru.Hru_data_hru.delete().execute()
		hru.Hru_lte_hru.delete().execute()
		soils.Nutrients_sol.delete().execute()

		init.Plant_ini_item.delete().execute()
		init.Plant_ini.delete().execute()
		lum.Landuse_lum.delete().execute()
		lum.Management_sch.delete().execute()
		lum.Management_sch_auto.delete().execute()

		regions.Ls_unit_ele.delete().execute()
		regions.Ls_unit_def.delete().execute()

		connect.Rout_unit_con.delete().execute()
		connect.Rout_unit_con_out.delete().execute()
		connect.Aquifer_con.delete().execute()
		connect.Aquifer_con_out.delete().execute()
		connect.Channel_con.delete().execute()
		connect.Channel_con_out.delete().execute()
		connect.Chandeg_con.delete().execute()
		connect.Chandeg_con_out.delete().execute()
		connect.Reservoir_con.delete().execute()
		connect.Reservoir_con_out.delete().execute()
		connect.Exco_con.delete().execute()
		connect.Exco_con_out.delete().execute()
		connect.Recall_con.delete().execute()
		connect.Recall_con_out.delete().execute()
		connect.Hru_con.delete().execute()
		connect.Hru_con_out.delete().execute()
		connect.Hru_lte_con.delete().execute()
		connect.Hru_lte_con_out.delete().execute()

	def update_gis_water(self):
		conn = db_lib.open_db(self.project_db_file)
		cols = db_lib.get_column_names(conn, 'gis_water')
		col_names = [v['name'] for v in cols]
		if 'subbasin' not in col_names:
			migrator = SqliteMigrator(SqliteDatabase(self.project_db_file))
			migrate(
				#migrator.add_column('gis_water', 'subbasin', IntegerField(default=0))
				migrator.rename_table('gis_water', 'gis_water2'),
				migrator.add_column('gis_water2', 'subbasin', IntegerField(default=0))
			)
			db_lib.execute_non_query(self.project_db_file, 'create table gis_water (id INTEGER PRIMARY KEY UNIQUE NOT NULL, wtype TEXT, lsu INTEGER, subbasin INTEGER, area REAL, xpr REAL, ypr REAL, lat REAL, lon REAL, elev REAL)')
			db_lib.execute_non_query(self.project_db_file, 'insert into gis_water select id, wtype, lsu, subbasin, area, xpr, ypr, lat, lon, elev from gis_water2')
			db_lib.execute_non_query(self.project_db_file, 'drop table gis_water2')

			for water in gis.Gis_water.select():
				channel_id = water.lsu // 10
				channel = gis.Gis_channels.get_or_none(gis.Gis_channels.id == channel_id)
				if channel is not None:
					water.subbasin = channel.subbasin
					water.save()
				else:
					raise ValueError('Subbasin not found for row in gis_water with id {}. Please update your project to use the latest version of QSWAT+.'.format(water.id))
		
	def update_plants(self):
		any_missing = False
		cols_to_check = [
			'gro_trig',
			'nfix_co',
			'leaf_tov_mx',
			'leaf_tov_mn',
			'dlai_rate'
		]
		
		conn = db_lib.open_db(self.project_db_file)
		cols = db_lib.get_column_names(conn, 'plants_plt')
		col_names = [v['name'] for v in cols]
		
		for col in cols_to_check:
			if col not in col_names:
				any_missing = True
				break
				
		if any_missing:
			if db_lib.exists_table(conn, 'plants_plt'):
				db_lib.delete_table(self.project_db_file, 'plants_plt')
				self.project_db.create_tables([hru_parm_db.Plants_plt])
				db_lib.copy_table('plants_plt', self.reference_db_file, self.project_db_file)

	def insert_routing_units(self):
		"""
		Insert routing unit SWAT+ tables from GIS database.
		"""
		cnt = get_max_id(gis.Gis_lsus)
		if routing_unit.Rout_unit_rtu.select().count() == 0:
			topography = []
			fields = []
			rout_units = []
			rout_unit_cons = []

			i = 1
			for row in gis.Gis_lsus.select().order_by(gis.Gis_lsus.id):
				self.gis_to_rtu_ids[row.id] = i

				rtu_name = get_name('rtu', row.id, cnt)
				lat = row.lat
				lon = row.lon
				area = row.area
				slp_len = self.get_slope_len(row.slope / 100)

				topo = {
					'id': i,
					'name': get_name('toportu', row.id, cnt),
					'slp': row.slope / 100,
					'slp_len': slp_len,
					'lat_len': slp_len,
					'dist_cha': 121.0,
					'depos': 0,
					'type': 'sub'
				}
				topography.append(topo)

				field = {
					'id': i,
					'name': get_name('fld', row.id, cnt),
					'len': 500,
					'wd': 100,
					'ang': 30
				}
				fields.append(field)

				rtu = {
					'id': i,
					'name': rtu_name,
					'topo': i,
					'field': i
				}
				rout_units.append(rtu)

				rtu_con = {
					'rtu': i,
					'id': i,
					'name': rtu_name,
					'gis_id': row.id,
					'elev': row.elev,
					'lat': lat,
					'lon': lon,
					'area': area,
					'ovfl': 0,
					'rule': 0
				}
				rout_unit_cons.append(rtu_con)

				i += 1

			db_lib.bulk_insert(self.project_db, hydrology.Topography_hyd, topography)
			db_lib.bulk_insert(self.project_db, hydrology.Field_fld, fields)
			db_lib.bulk_insert(self.project_db, routing_unit.Rout_unit_rtu, rout_units)
			db_lib.bulk_insert(self.project_db, connect.Rout_unit_con, rout_unit_cons)

	def insert_om_water(self):
		db_lib.bulk_insert(self.project_db, init.Om_water_ini, init.Om_water_ini.get_default_data())

	def insert_aquifers(self):
		cnt = gis.Gis_subbasins.select().count() * 10
		if aquifer.Aquifer_aqu.select().count() == 0:
			init_aqu = aquifer.Initial_aqu.create(
				name='initaqu1',
				org_min=1
			)

			aquifer_aqus = []
			aquifer_cons = []
			aquifer_con_outs = []

			i = 1
			for row in gis.Gis_subbasins.select().order_by(gis.Gis_subbasins.id):
				channels_in_sub = gis.Gis_channels.select(gis.Gis_channels.id).where(gis.Gis_channels.subbasin == row.id)
				channel_ids = [v.id for v in channels_in_sub]

				# Add floodplain aquifer
				flood = gis.Gis_lsus.select(fn.SUM(gis.Gis_lsus.area).alias('tot_area')).where((gis.Gis_lsus.category != 2) & (gis.Gis_lsus.channel << channel_ids)).get()
				flood_id = i
				has_flood = flood is not None and flood.tot_area is not None
				if has_flood:
					self.aqu_id_to_sub[i] = row.id
					self.sub_to_flood_aqu_id[row.id] = i
					for c in channel_ids:
						self.gis_to_flood_aqu_ids[c] = i

					cat = gis.Gis_lsus.select(gis.Gis_lsus.category).where(gis.Gis_lsus.category != 2).get().category

					aqu_gisid = row.id * 10 + cat
					aqu_name = get_name('aqu', aqu_gisid, cnt)
					aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_shallow(i, aqu_name, init_aqu.id))
					aqu_con = {
						'aqu': i,
						'id': i,
						'name': aqu_name,
						'gis_id': aqu_gisid,
						'lat': row.lat,
						'lon': row.lon,
						'area': flood.tot_area,
						'elev': row.elev,
						'ovfl': 0,
						'rule': 0
					}
					aquifer_cons.append(aqu_con)

					end_cha = channels_in_sub.order_by(gis.Gis_channels.areac.desc()).get()

					aqu_con_out = {
						'aquifer_con': i,
						'order': 1,
						'obj_typ': 'sdc',
						'obj_id': self.gis_to_cha_ids[end_cha.id],
						'hyd_typ': 'tot',
						'frac': 1.0
					}
					aquifer_con_outs.append(aqu_con_out)
					i += 1

				# Add upland aquifer, if any upland LSUs
				upland = gis.Gis_lsus.select(fn.SUM(gis.Gis_lsus.area).alias('tot_area')).where((gis.Gis_lsus.category == 2) & (gis.Gis_lsus.channel << channel_ids)).get()
				has_upland = upland is not None and upland.tot_area is not None
				if has_upland:
					self.aqu_id_to_sub[i] = row.id
					self.sub_to_upland_aqu_id[row.id] = i
					for c in channel_ids:
						self.gis_to_upland_aqu_ids[c] = i

					aqu_gisid = row.id * 10 + 2
					aqu_name = get_name('aqu', aqu_gisid, cnt)
					aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_shallow(i, aqu_name, init_aqu.id))
					aqu_con = {
						'aqu': i,
						'id': i,
						'name': aqu_name,
						'gis_id': aqu_gisid,
						'lat': row.lat,
						'lon': row.lon,
						'area': upland.tot_area,
						'elev': row.elev,
						'ovfl': 0,
						'rule': 0
					}
					aquifer_cons.append(aqu_con)

					if has_flood:
						aqu_con_out = {
							'aquifer_con': i,
							'order': 1,
							'obj_typ': 'aqu',
							'obj_id': flood_id,
							'hyd_typ': 'tot',
							'frac': 1.0
						}
						aquifer_con_outs.append(aqu_con_out)
					i += 1

				# Add an aquifer if no flood or upland
				if not (has_flood or has_upland):
					self.aqu_id_to_sub[i] = row.id
					self.sub_to_flood_aqu_id[row.id] = i
					for c in channel_ids:
						self.gis_to_flood_aqu_ids[c] = i

					aqu_gisid = row.id * 10
					aqu_name = get_name('aqu', aqu_gisid, cnt)
					aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_shallow(i, aqu_name, init_aqu.id))
					aqu_con = {
						'aqu': i,
						'id': i,
						'name': aqu_name,
						'gis_id': aqu_gisid,
						'lat': row.lat,
						'lon': row.lon,
						'area': row.area,
						'elev': row.elev,
						'ovfl': 0,
						'rule': 0
					}
					aquifer_cons.append(aqu_con)

					if len(channel_ids) > 0:
						end_cha = channels_in_sub.order_by(gis.Gis_channels.areac.desc()).get()
						aqu_con_out = {
							'aquifer_con': i,
							'order': 1,
							'obj_typ': 'sdc',
							'obj_id': self.gis_to_cha_ids[end_cha.id],
							'hyd_typ': 'tot',
							'frac': 1.0
						}
						aquifer_con_outs.append(aqu_con_out)
					else:
						matching_res = gis.Gis_water.select().where((gis.Gis_water.wtype == 'RES') & (gis.Gis_water.subbasin == row.id))
						add_con_out = False
						if matching_res.count() > 0:
							end_res = matching_res.get()
							obj_id = self.gis_to_res_ids[end_res.id]
							obj_typ = 'res'
							add_con_out = True
						else:
							# Try and see if sub routes to a reservoir or channel
							sub_route = gis.Gis_routing.find_from_source(RouteCat.SUB, row.id)
							route = self.get_gis_route(sub_route.sourcecat, sub_route.sourceid, RouteCat.PT)
							if route is not None:
								if route.sinkcat == RouteCat.RES:
									add_con_out = True
									end_res = gis.Gis_water.get(gis.Gis_water.id == route.sinkid)
									obj_id = self.gis_to_res_ids[end_res.id]
									obj_typ = 'res'
								elif route.sinkcat == RouteCat.CH:
									add_con_out = True
									end_cha = gis.Gis_channels.get(gis.Gis_channels.id == route.sinkid)
									obj_id = self.gis_to_cha_ids[end_cha.id]
									obj_typ = 'sdc'
						
						if add_con_out:
							aqu_con_out = {
								'aquifer_con': i,
								'order': 1,
								'obj_typ': obj_typ,
								'obj_id': obj_id,
								'hyd_typ': 'tot',
								'frac': 1.0
							}
							aquifer_con_outs.append(aqu_con_out)

					i += 1

			# Add deep aquifers for each outlet
			outlet_sub_map = self.get_outlet_sub_map()
			deep_cons = []
			sub_to_deep = {}
			cnt = len(outlet_sub_map)
			for sub, outlets in outlet_sub_map.items():
				for o in outlets:
					sub_to_deep[o] = i
				
				name = get_name('aqu_deep', sub, cnt)
				aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_deep(i, name, init_aqu.id))

				bsn_area = 0
				if len(outlets) < 900:
					bsn_area = gis.Gis_subbasins.select(fn.Sum(gis.Gis_subbasins.area)).where(gis.Gis_subbasins.id << outlets).scalar()
				else:
					for s in gis.Gis_subbasins.select():
						if s.id in outlets:
							bsn_area += s.area

				subbasin = gis.Gis_subbasins.get_or_none(gis.Gis_subbasins.id == sub)

				if subbasin is None:
					raise ValueError('Subbasin {} does not exist.'.format(sub))

				deep_con = {
					'aqu': i,
					'id': i,
					'name': name,
					'gis_id': sub,
					'lat': subbasin.lat,
					'lon': subbasin.lon,
					'area': bsn_area if bsn_area is not None else 0,
					'elev': subbasin.elev,
					'ovfl': 0,
					'rule': 0
				}

				deep_cons.append(deep_con)
				i += 1

			for con in aquifer_cons:
				sub = self.aqu_id_to_sub[con['id']]
				if sub in sub_to_deep:
					deep_id =sub_to_deep[sub]
					aqu_con_out = {
						'aquifer_con': con['id'],
						'order': 2,
						'obj_typ': 'aqu',
						'obj_id': deep_id,
						'hyd_typ': 'rhg',
						'frac': 1.0
					}
					aquifer_con_outs.append(aqu_con_out)

			aquifer_cons.extend(deep_cons)

			db_lib.bulk_insert(self.project_db, aquifer.Aquifer_aqu, aquifer_aqus)
			db_lib.bulk_insert(self.project_db, connect.Aquifer_con, aquifer_cons)
			db_lib.bulk_insert(self.project_db, connect.Aquifer_con_out, aquifer_con_outs)

	def get_gis_route(self, sourcecat, sourceid, keep_searching_cat):
		route = gis.Gis_routing.find_from_source(sourcecat, sourceid)
		if route is not None and route.sinkcat == keep_searching_cat:
			return self.get_gis_route(route.sinkcat, route.sinkid, keep_searching_cat)
		return route

	def get_outlet_sub_map(self):
		outlets = gis.Gis_routing.select().where(gis.Gis_routing.sinkcat == RouteCat.OUTLET)
		outlet_sub_ids = []
		outlet_sub_map = {}
		for outlet in outlets:
			outlet_sub = gis.Gis_routing.get_or_none((gis.Gis_routing.sinkcat == outlet.sourcecat) & (gis.Gis_routing.sinkid == outlet.sourceid) & (gis.Gis_routing.sourcecat == RouteCat.SUB))
			if outlet_sub is None:
				outlet_res = gis.Gis_routing.get_or_none((gis.Gis_routing.sinkcat == outlet.sourcecat) & (gis.Gis_routing.sinkid == outlet.sourceid) & (gis.Gis_routing.sourcecat << RouteCat.WaterTypes))
				if outlet_res is not None:
					outlet_sub = gis.Gis_routing.get_or_none((gis.Gis_routing.sinkcat == outlet_res.sourcecat) & (gis.Gis_routing.sinkid == outlet_res.sourceid) & (gis.Gis_routing.sourcecat == RouteCat.SUB))

			if outlet_sub is not None:
				outlet_sub_ids.append(outlet_sub.sourceid)
				outlet_sub_map[outlet_sub.sourceid] = []

		num_outlets = len(outlet_sub_ids)
		
		if num_outlets == 0:
			raise ValueError("No watershed outlets found.")
		elif num_outlets == 1:
			all_subs = gis.Gis_subbasins.select(gis.Gis_subbasins.id)
			outlet_sub_map[outlet_sub_ids[0]] = [m.id for m in all_subs]
		else:
			sub_routes = gis.Gis_routing.select().where((gis.Gis_routing.sourcecat == RouteCat.SUB) & (gis.Gis_routing.sourceid.not_in(outlet_sub_ids)))
			for sub_route in sub_routes:
				current_subid = sub_route.sourceid
				searchcat = sub_route.sinkcat
				searchid = sub_route.sinkid
				keep_searching = True
				too_many = 1000000
				tries = 1
				temp_subs = []
				while keep_searching:
					out_route = gis.Gis_routing.find_from_source(searchcat, searchid)
					if out_route is None:
						keep_searching = False
					elif out_route.sinkcat == RouteCat.CH:
						channel = gis.Gis_channels.get_or_none(gis.Gis_channels.id == out_route.sinkid)
						if channel is None:
							keep_searching = False
						else:	
							temp_subs.append(channel.subbasin)						
							if channel.subbasin in outlet_sub_ids:
								outlet_sub_map[channel.subbasin].append(current_subid)
								outlet_sub_map[channel.subbasin].extend(temp_subs)
								temp_subs = []
								keep_searching = False
							else:
								searchcat = RouteCat.SUB
								searchid = channel.subbasin
					elif out_route.sinkcat in RouteCat.WaterTypes:
						water = gis.Gis_water.get_or_none(gis.Gis_water.id == out_route.sinkid)
						if water is None:
							keep_searching = False
						else:
							water_sub = water.subbasin #water.get_subbasin_id(self.project_db_file)
							temp_subs.append(water_sub)						
							if water.subbasin in outlet_sub_ids:
								outlet_sub_map[water_sub].append(current_subid)
								outlet_sub_map[water_sub].extend(temp_subs)
								temp_subs = []
								keep_searching = False
							else:
								searchcat = RouteCat.SUB
								searchid = water_sub
					else:
						searchcat = out_route.sinkcat
						searchid = out_route.sinkid	

					tries += 1
					if tries > too_many:
						raise ValueError("Error in routing table: infinite looping")		
		
		for key in outlet_sub_map:
			outlet_sub_map[key].append(key)
			outlet_sub_map[key] = list(dict.fromkeys(outlet_sub_map[key]))
		return outlet_sub_map

	def insert_channels_lte(self):
		"""
		Insert channel lte SWAT+ tables from GIS database.
		"""
		cnt = get_max_id(gis.Gis_channels)
		if channel.Channel_lte_cha.select().count() == 0:
			init = channel.Initial_cha.create(
				name='initcha1',
				org_min=1
			)

			nut = channel.Nutrients_cha.create(
				name='nutcha1',
				plt_n=0,
				ptl_p=0,
				alg_stl=1,
				ben_disp=0.05,
				ben_nh3n=0.5,
				ptln_stl=0.05,
				ptlp_stl=0.05,
				cst_stl=2.5,
				ben_cst=2.5,
				cbn_bod_co=1.71,
				air_rt=50,
				cbn_bod_stl=0.36,
				ben_bod=2,
				bact_die=2,
				cst_decay=1.71,
				nh3n_no2n=0.55,
				no2n_no3n=1.1,
				ptln_nh3n=0.21,
				ptlp_solp=0.35,
				q2e_lt=2,
				q2e_alg=2,
				chla_alg=50,
				alg_n=0.08,
				alg_p=0.015,
				alg_o2_prod=1.6,
				alg_o2_resp=2,
				o2_nh3n=3.5,
				o2_no2n=1.07,
				alg_grow=2,
				alg_resp=2.5,
				slr_act=0.3,
				lt_co=0.75,
				const_n=0.02,
				const_p=0.025,
				lt_nonalg=1,
				alg_shd_l=0.03,
				alg_shd_nl=0.054,
				nh3_pref=0.5
			)

			hydrology_chas = []
			channel_chas = []
			channel_cons = []

			i = 1
			for row in gis.Gis_channels.select().order_by(gis.Gis_channels.id):
				self.gis_to_cha_ids[row.id] = i

				cha_name = get_name('cha', row.id, cnt)
				aqu_name = get_name('aqu', row.id, cnt)

				lat = None
				lon = None

				try:
					lsu_coords = gis.Gis_lsus.select(
							fn.AVG(gis.Gis_lsus.lat).alias('avg_lat'),
							fn.AVG(gis.Gis_lsus.lon).alias('avg_lon')
						).where(gis.Gis_lsus.channel == row.id).get()

					lat = lsu_coords.avg_lat
					lon = lsu_coords.avg_lon
				except gis.Gis_lsus.DoesNotExist:
					pass

				if lat is None or lon is None:
					try:
						pt = gis.Gis_points.get(gis.Gis_points.subbasin == row.subbasin)
						lat = pt.lat
						lon = pt.lon
					except gis.Gis_points.DoesNotExist:
						pass
					except IndexError:
						pass

				if lat is None: lat = 0
				if lon is None: lon = 0

				# Channel tables
				hyd_cha = {
					'id': i,
					'name': 'hyd%s' % cha_name,
					'order': 'first',
					'wd': row.wid2,
					'dp': row.dep2,
					'slp': row.slo2 / 100,
					'len': row.len2 / 1000,
					'mann': 0.05,
					'k': 1,
					'erod_fact': 0.01,
					'cov_fact': 0.005,
					'hc_cov': 0,
					'eq_slp': 0.001,
					'd50': 12,
					'clay': 50,
					'carbon': 0.04,
					'dry_bd': 1,
					'side_slp': 0.5,
					'bed_load': 0.5,
					't_conc': 10,
					'shear_bnk': 0.75,
					'hc_erod': 0.1,
					'hc_ht': 0.3,
					'hc_len': 0.3
				}
				hydrology_chas.append(hyd_cha)

				chan_cha = {
					'id': i,
					'name': cha_name,
					'hyd': i,
					'init': init.id,
					'nut': nut.id
				}
				channel_chas.append(chan_cha)

				chan_con = {
					'lcha': i,
					'id': i,
					'name': cha_name,
					'gis_id': row.id,
					'lat': lat,
					'lon': lon,
					'area': row.areac,
					'ovfl': 0,
					'rule': 0
				}
				channel_cons.append(chan_con)

				i += 1

			db_lib.bulk_insert(self.project_db, channel.Hyd_sed_lte_cha, hydrology_chas)
			db_lib.bulk_insert(self.project_db, channel.Channel_lte_cha, channel_chas)
			db_lib.bulk_insert(self.project_db, connect.Chandeg_con, channel_cons)

	def insert_reservoirs(self):
		"""
		Insert reservoir SWAT+ tables from GIS database.
		"""
		cnt = get_max_id(gis.Gis_water)
		if reservoir.Reservoir_res.select().count() == 0:
			res_query = gis.Gis_water.select().order_by(gis.Gis_water.id)
			if res_query.count() > 0:
				init = reservoir.Initial_res.create(
					name='initres1',
					org_min=1
				)

				nut = reservoir.Nutrients_res.create(
					name='nutres1',
					mid_start=5,
					mid_end=10,
					mid_n_stl=5.5,
					n_stl=5.5,
					mid_p_stl=10,
					p_stl=10,
					chla_co=1,
					secchi_co=1,
					theta_n=1,
					theta_p=1,
					n_min_stl=0.1,
					p_min_stl=0.01
				)

				sed = reservoir.Sediment_res.create(
					name='sedres1',
					sed_amt=1,
					d50=10,
					carbon=0,
					bd=0,
					sed_stl=1,
					stl_vel=1
				)

				reservoir.Weir_res.create(
					name='shape1',
					num_steps=24,
					disch_co=1,
					energy_co=150000,
					weir_wd=2,
					vel_co=1.75,
					dp_co=1
				)

				hydrology_res = []
				reservoir_res = []
				reservoir_cons = []

				res_rel = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'corps_med_res')
				res_rel_id = None
				if res_rel is not None:
					res_rel_id = res_rel.id

				i = 1
				for row in res_query:
					self.gis_to_res_ids[row.id] = i
					res_name = get_name(row.wtype.lower(), row.id, cnt)

					hyd_res = {
						'id': i,
						'name': res_name,
						'yr_op': 1,
						'mon_op': 1,
						'area_ps': row.area,
						'vol_ps': row.area * 10,
						'area_es': row.area * 1.15,
						'vol_es': row.area * 1.15 * 10,
						'k': 0,
						'evap_co': 0.6,
						'shp_co1': 0,
						'shp_co2': 0
					}
					hydrology_res.append(hyd_res)

					res = {
						'id': i,
						'name': res_name,
						'rel': res_rel_id,  # corps_med_res in d_table_dtl
						'hyd': i,
						'init': init.id,
						'sed': sed.id,
						'nut': nut.id
					}
					reservoir_res.append(res)

					res_con = {
						'res': i,
						'id': i,
						'name': res_name,
						'gis_id': row.id,
						'lat': row.lat,
						'lon': row.lon,
						'elev': row.elev,
						'area': row.area,
						'ovfl': 0,
						'rule': 0
					}
					reservoir_cons.append(res_con)

					i += 1

				db_lib.bulk_insert(self.project_db, reservoir.Hydrology_res, hydrology_res)
				db_lib.bulk_insert(self.project_db, reservoir.Reservoir_res, reservoir_res)
				db_lib.bulk_insert(self.project_db, connect.Reservoir_con, reservoir_cons)

	def insert_exco(self, is_lte_cha_type=False):
		"""
		Insert exco (constant point source) SWAT+ tables from GIS database.
		"""
		if exco.Exco_exc.select().count() == 0:
			exco_query = gis.Gis_points.select().where((gis.Gis_points.ptype == 'P') | (gis.Gis_points.ptype == 'I')).order_by(gis.Gis_points.id)

			cnt = get_max_id(gis.Gis_points)
			if exco_query.count() > 0:
				exco_cons = []
				exco_con_outs = []

				exco.Exco_om_exc.create(
					name='exco_om1',
					flo=0,
					sed=0,
					orgn=0,
					sedp=0,
					no3=0,
					solp=0,
					chla=0,
					nh3=0,
					no2=0,
					cbod=0,
					dox=0,
					sand=0,
					silt=0,
					clay=0,
					sag=0,
					lag=0,
					gravel=0,
					tmp=0
				)

				exco.Exco_exc.create(
					id=1,
					name="rec_const",
					om=1
				)

				i = 1
				for row in exco_query:
					rec_name = get_name('pt', row.id, cnt)

					exco_con = {
						'exco': 1,
						'id': i,
						'name': rec_name,
						'gis_id': row.id,
						'lat': row.lat,
						'lon': row.lon,
						'elev': row.elev,
						'area': 0,
						'ovfl': 0,
						'rule': 0
					}
					exco_cons.append(exco_con)

					used = dict()
					for con in gis.Gis_routing.select().where(
						(gis.Gis_routing.sourcecat == RouteCat.PT) & (gis.Gis_routing.sourceid == row.id)):
						if con.sourceid in used:
							used[i] += 1
						else:
							used[i] = 1

						con_out = self.get_con_out(con.sinkid, con.sinkcat, con.percent, used[i], 'exco_con', i, is_lte_cha_type=is_lte_cha_type)
						if con_out is not None:
							exco_con_outs.extend(con_out)

					i += 1

				db_lib.bulk_insert(self.project_db, connect.Exco_con, exco_cons)
				db_lib.bulk_insert(self.project_db, connect.Exco_con_out, exco_con_outs)

	def insert_recall(self, is_lte_cha_type=False):
		"""
		Insert recall (point source) SWAT+ tables from GIS database.
		"""
		if recall.Recall_rec.select().count() == 0:
			rec_query = gis.Gis_points.select().where(
				(gis.Gis_points.ptype == 'P') | (gis.Gis_points.ptype == 'I')).order_by(gis.Gis_points.id)

			cnt = get_max_id(gis.Gis_points)
			if rec_query.count() > 0:
				rec_cons = []
				rec_con_outs = []
				recs = []
				rec_data = []

				i = 1
				for row in rec_query:
					rec_name = get_name('pt', row.id, cnt)

					rec_con = {
						'rec': i,
						'id': i,
						'name': rec_name,
						'gis_id': row.id,
						'lat': row.lat,
						'lon': row.lon,
						'elev': row.elev,
						'area': 0,
						'ovfl': 0,
						'rule': 0
					}
					rec_cons.append(rec_con)

					rec = {
						'id': i,
						'name': rec_name,
						'rec_typ': 4
					}
					recs.append(rec)

					data = {
						'recall_rec_id': i,
						'yr': 0,
						't_step': 0,
						'flo': 0,
						'sed': 0,
						'ptl_n': 0,
						'ptl_p': 0,
						'no3_n': 0,
						'sol_p': 0,
						'chla': 0,
						'nh3_n': 0,
						'no2_n': 0,
						'cbn_bod': 0,
						'oxy': 0,
						'sand': 0,
						'silt': 0,
						'clay': 0,
						'sm_agg': 0,
						'lg_agg': 0,
						'gravel': 0,
						'tmp': 0
					}
					rec_data.append(data)

					used = dict()
					for con in gis.Gis_routing.select().where(
						(gis.Gis_routing.sourcecat == RouteCat.PT) & (gis.Gis_routing.sourceid == row.id)):
						if con.sourceid in used:
							used[i] += 1
						else:
							used[i] = 1

						con_out = self.get_con_out(con.sinkid, con.sinkcat, con.percent, used[i], 'recall_con', i, is_lte_cha_type=is_lte_cha_type)
						if con_out is not None:
							rec_con_outs.extend(con_out)

					i += 1

				db_lib.bulk_insert(self.project_db, connect.Recall_con, rec_cons)
				db_lib.bulk_insert(self.project_db, connect.Recall_con_out, rec_con_outs)
				db_lib.bulk_insert(self.project_db, recall.Recall_rec, recs)
				db_lib.bulk_insert(self.project_db, recall.Recall_dat, rec_data)

	def copy_mgt(self, ds_mgt, plant_name):
		m = lum.Management_sch.create(
			name='{mgt}_{p}'.format(mgt=ds_mgt.name, p=plant_name)
		)

		for a in ds_mgt.auto_ops:
			lum.Management_sch_auto.create(
				management_sch=m.id,
				d_table=a.d_table.id
			)

		for o in ds_mgt.operations:
			op_data1 = o.op_data1
			if o.op_typ in ['plnt', 'harv', 'hvkl']:
				op_data1 = plant_name

			lum.Management_sch_op.create(
				management_sch=m.id,
				op_typ=o.op_typ,
				mon=o.mon,
				day=o.day,
				hu_sch=o.hu_sch,
				op_data1=op_data1,
				op_data2=o.op_data2,
				op_data3=o.op_data3,
				description=o.description,
				order=o.order
			)

		return m.id

	def insert_d_table(self, plant_name, compare_table_name):
		return GisImport.insert_decision_table(plant_name, compare_table_name)

	@staticmethod
	def insert_decision_table(plant_name, compare_table_name):
		existing_table = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == compare_table_name)
		if existing_table is not None:
			new_d_tbl_name = 'pl_hv_{plant}'.format(plant=plant_name)
			curr_table = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == new_d_tbl_name)
			if curr_table is None:
				new_id = decision_table.D_table_dtl.insert(
					name=new_d_tbl_name,
					file_name='lum.dtl'
				).execute()

				for cond in existing_table.conditions:
					cond_id = decision_table.D_table_dtl_cond.insert(
						d_table=new_id,
						var=cond.var,
						obj=cond.obj,
						obj_num=cond.obj_num,
						lim_var=cond.lim_var,
						lim_op=cond.lim_op,
						lim_const=cond.lim_const
					).execute()

					for alt in cond.alts:
						decision_table.D_table_dtl_cond_alt.insert(
							cond=cond_id,
							alt=alt.alt
						).execute()
				
				for act in existing_table.actions:
					name = act.name
					if act.act_typ == 'plant':
						name = 'plant_{name}'.format(name=plant_name)
					
					option = act.option
					if act.option == 'corn' or act.option == 'wwht':
						option = plant_name

					act_id = decision_table.D_table_dtl_act.insert(
						d_table=new_id,
						act_typ=act.act_typ,
						obj=act.obj,
						obj_num=act.obj_num,
						name=name,
						option=option,
						const=act.const,
						const2=act.const2,
						fp=act.fp
					).execute()

					for oc in act.outcomes:
						decision_table.D_table_dtl_act_out.insert(
							act=act_id,
							outcome=oc.outcome
						).execute()
				
				return new_id
			else:
				return curr_table.id
		return None

	def insert_landuse(self):
		"""
		Insert default plant.ini and landuse.lum for any plants and urbans that don't already have one.
		"""
		lum_default_cal_group = None #"all_lum"
		lum_default_mgt = None #lum.Management_sch.get(lum.Management_sch.name == 'no_mgt').id
		lum_default_cn2 = 5
		lum_default_cons_prac = 1
		lum_default_ov_mann = 2

		#default_mgts = ['agrr', 'agrc', 'ag_P_fert', 'ag_tree', 'ag_veg', 'managed_past', 'ag_spring']

		distinct_lu = gis.Gis_hrus.select(gis.Gis_hrus.landuse).distinct()
		lus = [item.landuse.lower() for item in distinct_lu]
		for lu in lus:
			try:
				plant = hru_parm_db.Plants_plt.get(hru_parm_db.Plants_plt.name ** lu)
				p_id = plant.id

				lum_name = '{name}_lum'.format(name=lu)
				comm_name = '{name}_comm'.format(name=lu)
				try:
					pcom = None
					if lu != 'barr':
						ds_pi = ds_init.Plant_ini.get(ds_init.Plant_ini.name == comm_name)
						pi = init.Plant_ini.create(
							name=ds_pi.name,
							rot_yr_ini=ds_pi.rot_yr_ini
						)
						pcom = pi.id

						for p in ds_pi.plants:
							init.Plant_ini_item.create(
								plant_ini=pi.id,
								plnt_name=p_id,
								lc_status=p.lc_status,
								lai_init=p.lai_init,
								bm_init=p.bm_init,
								phu_init=p.phu_init,
								plnt_pop=p.plnt_pop,
								yrs_init=p.yrs_init,
								rsd_init=p.rsd_init
							)

					ds_m = ds_lum.Landuse_lum.get(ds_lum.Landuse_lum.name == lum_name)

					"""mgt_id = ds_m.mgt.id
					if ds_m.mgt.name in default_mgts:
						mgt_id = self.copy_mgt(ds_m.mgt, lu)"""

					mgt_id = None
					new_d_table_id = None
					if plant.plnt_typ == 'warm_annual':
						new_d_table_id = self.insert_d_table(plant.name, 'pl_hv_corn')
					elif plant.plnt_typ == 'cold_annual':
						new_d_table_id = self.insert_d_table(plant.name, 'pl_hv_wwht')

					if new_d_table_id is not None:
						mgt_name = '{plant}_rot'.format(plant=plant.name)
						curr_mgt = lum.Management_sch.get_or_none(lum.Management_sch.name == mgt_name)
						if curr_mgt is not None:
							mgt_id = curr_mgt.id
						else:
							mgt_id = lum.Management_sch.insert(
								name = mgt_name
							).execute()
							lum.Management_sch_auto.insert(
								management_sch=mgt_id,
								d_table=new_d_table_id
							).execute()

					lum.Landuse_lum.create(
						name=ds_m.name,
						plnt_com=pcom,
						mgt=mgt_id,
						cn2=ds_m.cn2.id,
						cons_prac=ds_m.cons_prac.id,
						ov_mann=ds_m.ov_mann.id,
						cal_group=ds_m.cal_group
					)

				except ds_init.Plant_ini.DoesNotExist:
					pcom = None
					if lu != 'barr':
						pi = init.Plant_ini.create(
							name='{name}_comm'.format(name=lu),
							rot_yr_ini=1
						)
						pcom = pi.id

						init.Plant_ini_item.create(
							plant_ini=pi.id,
							plnt_name=p_id,
							lc_status=0,
							lai_init=0,
							bm_init=0,
							phu_init=0,
							plnt_pop=0,
							yrs_init=0,
							rsd_init=10000
						)

					lum.Landuse_lum.create(
						name='{name}_lum'.format(name=lu),
						plnt_com=pcom,
						mgt=lum_default_mgt,
						cn2=lum_default_cn2,
						cons_prac=lum_default_cons_prac,
						ov_mann=lum_default_ov_mann,
						cal_group=lum_default_cal_group
					)

			except hru_parm_db.Plants_plt.DoesNotExist:
				try:
					u = hru_parm_db.Urban_urb.get(hru_parm_db.Urban_urb.name ** lu)

					lum.Landuse_lum.create(
						name='{name}_lum'.format(name=lu),
						urban=u.id,
						urb_ro='buildup_washoff',
						mgt=lum_default_mgt,
						cn2=49,
						cons_prac=lum_default_cons_prac,
						ov_mann=18,
						cal_group=lum_default_cal_group
					)
				except hru_parm_db.Urban_urb.DoesNotExist:
					raise ValueError('{name} does not exist in plants_plt or urban_urb, but is used as land use in your GIS HRUs.'.format(name=lu))

		lum_dict = {}
		for lu in lus:
			l = lum.Landuse_lum.get(lum.Landuse_lum.name.contains(lu))
			lum_dict[lu] = l.id

		return lum_dict

	def insert_hrus(self):
		"""
		Insert hru_data.hru SWAT+ data from GIS database.
		"""
		lum_dict = self.insert_landuse()

		# Create default nutrients.sol
		nut = soils.Nutrients_sol.create(
			name='soilnut1',
			dp_co=13.00,
			tot_n=6.00,
			min_n=3.00,
			org_n=3.00,
			tot_p=3.50,
			min_p=0.40,
			org_p=0.15,
			sol_p=0.25,
			h3a_p=1.20,
			mehl_p=0.85,
			bray_p=0.85
		)

		sp = init.Soil_plant_ini.create(
			name='soilplant1',
			sw_frac=0,
			nutrients=nut.id
		)

		hyds = []
		hrus = []
		topos = []
		hru_cons = []
		elem_subs = []
		lsu_eles = []

		wetlands = []
		hyd_wets = []

		bsn_area = gis.Gis_subbasins.select(fn.Sum(gis.Gis_subbasins.area)).scalar()

		cnt = get_max_id(gis.Gis_hrus)
		topo_id = hydrology.Topography_hyd.select().count() + 1
		i = 1
		wi = 1
		for row in gis.Gis_hrus.select():
			hru_name = get_name('hru', row.id, cnt)

			hyd = {
				'id': i,
				'name': get_name('hyd', row.id, cnt),
				'lat_ttime': 0.00,
				'lat_sed': 0.00,
				'can_max': 1.00,
				'esco': 0.95,
				'epco': 1.00,
				'orgn_enrich': 0.00,
				'orgp_enrich': 0.00,
				'evap_pothole': 0.50,
				'bio_mix': 0.20,
				'perco': 0.50,
				'lat_orgn': 0.00,
				'lat_orgp': 0.00,
				'harg_pet': 0.00,
				'cn_plntet': 1.00
			}
			hyds.append(hyd)

			slp_len = self.get_slope_len(row.slope)

			topo = {
				'id': topo_id,
				'name': get_name('topohru', row.id, cnt),
				'slp': row.slope / 100,
				'slp_len': slp_len,
				'lat_len': slp_len,
				'dist_cha': 121.0,
				'depos': 0,
				'type': 'hru'
			}
			topos.append(topo)

			if row.landuse.lower() == 'watr':
				if wi == 1:
					res_rel = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'wetland')
					res_rel_id = None
					if res_rel is not None:
						res_rel_id = res_rel.id

					winit = reservoir.Initial_res.create(
						name='initwet1',
						org_min=1
					)

					wnut = reservoir.Nutrients_res.create(
						name='nutwet1',
						mid_start=5,
						mid_end=10,
						mid_n_stl=5.5,
						n_stl=5.5,
						mid_p_stl=10,
						p_stl=10,
						chla_co=1,
						secchi_co=1,
						theta_n=1,
						theta_p=1,
						n_min_stl=0.1,
						p_min_stl=0.01
					)

					wsed = reservoir.Sediment_res.create(
						name='sedwet1',
						sed_amt=1,
						d50=10,
						carbon=0,
						bd=0,
						sed_stl=1,
						stl_vel=1
					)
				
				hyd_wet = {
					'id': wi,
					'name': get_name('hydwet', row.id, cnt),
					'hru_ps': 0.1,
					'dp_ps': 20,
					'hru_es': 0.25,
					'dp_es': 100,
					'k': 0.01,
					'evap': 0.7,
					'vol_area_co': 1,
					'vol_dp_a': 1,
					'vol_dp_b': 1,
					'hru_frac': 0.5
				}
				hyd_wets.append(hyd_wet)

				wet = {
					'id': wi,
					'name': get_name('wet', row.id, cnt),
					'init': winit.id,
					'hyd': wi,
					'rel': res_rel_id,
					'sed': wsed.id,
					'nut': wnut.id
				}
				wetlands.append(wet)
				wi += 1

			hru_data = {
				'id': i,
				'name': hru_name,
				'topo': topo_id,
				'hydro': i,
				'lu_mgt': lum_dict[row.landuse.lower()],
				'soil_plant_init': sp.id,
				'snow': 1,
				'surf_stor': wi-1 if row.landuse.lower() == 'watr' else None
			}

			try:
				soil = soils.Soils_sol.get(soils.Soils_sol.name == row.soil)
				hru_data['soil'] = soil.id
			except soils.Soils_sol.DoesNotExist:
				raise ValueError('Soil "{s}" does not exist in your soils_sol table. Check your project in GIS and make '
								 'sure all soils from the gis_hrus table exist in soils_sol.'.format(s=row.soil))

			hrus.append(hru_data)
			topo_id += 1

			con = {
				'id': i,
				'hru': i,
				'name': hru_name,
				'gis_id': row.id,
				'elev': row.elev,
				'lat': row.lat,
				'lon': row.lon,
				'area': row.arslp,
				'ovfl': 0,
				'rule': 0
			}
			hru_cons.append(con)

			elem_sub = {
				'id': i,
				'name': hru_name,
				'rtu': self.gis_to_rtu_ids[row.lsu],
				'obj_typ': 'hru',
				'obj_id': i,
				'frac': row.arslp / row.arlsu
			}
			elem_subs.append(elem_sub)

			lsu_ele = {
				'id': i,
				'name': hru_name,
				'obj_typ': 'hru',
				'obj_typ_no': i,
				'bsn_frac': row.arslp / bsn_area,
				'sub_frac': row.arslp / row.arlsu,
				'reg_frac': 0,
				'ls_unit_def': self.gis_to_rtu_ids[row.lsu]
			}
			lsu_eles.append(lsu_ele)

			i += 1

		db_lib.bulk_insert(self.project_db, hydrology.Hydrology_hyd, hyds)
		db_lib.bulk_insert(self.project_db, hydrology.Topography_hyd, topos)
		db_lib.bulk_insert(self.project_db, hru.Hru_data_hru, hrus)
		db_lib.bulk_insert(self.project_db, connect.Hru_con, hru_cons)
		db_lib.bulk_insert(self.project_db, connect.Rout_unit_ele, elem_subs)
		db_lib.bulk_insert(self.project_db, regions.Ls_unit_ele, lsu_eles)
		db_lib.bulk_insert(self.project_db, reservoir.Hydrology_wet, hyd_wets)
		db_lib.bulk_insert(self.project_db, reservoir.Wetland_wet, wetlands)

	def insert_hru_ltes(self):
		distinct_lu = gis.Gis_hrus.select(gis.Gis_hrus.landuse).distinct()
		lus = [item.landuse.lower() for item in distinct_lu]
		plants = {}
		urbans = {}
		for lu in lus:
			try:
				plant = hru_parm_db.Plants_plt.get(hru_parm_db.Plants_plt.name ** lu)
				plants[lu] = plant
			except hru_parm_db.Plants_plt.DoesNotExist:
				try:
					u = hru_parm_db.Urban_urb.get(hru_parm_db.Urban_urb.name ** lu)
					urbans[lu] = u

					plant = hru_parm_db.Plants_plt.get(hru_parm_db.Plants_plt.name ** 'gras')
					plants[lu] = plant
				except hru_parm_db.Urban_urb.DoesNotExist:
					raise ValueError('{name} does not exist in plants_plt or urban_urb, but is used as land use in your GIS HRUs.'.format(name=lu))

		distinct_soils = gis.Gis_hrus.select(gis.Gis_hrus.soil).distinct()
		gs = [item.soil.lower() for item in distinct_soils]
		hru_soils = {}
		for s in gs:
			try:
				soil = soils.Soils_sol.get(soils.Soils_sol.name ** s)
				hru_soils[s] = soil
			except soils.Soils_sol.DoesNotExist:
				raise ValueError('{name} does not exist in soils_sol, but is used as soil in your GIS HRUs.'.format(name=s))

		trop_bounds = definitions.Tropical_bounds.get()

		pl_grow_sum = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_grow_sum')
		pl_end_sum = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_end_sum')
		pl_grow_win = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_grow_win')
		pl_end_win = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_end_win')

		if pl_grow_sum is None:
			raise ValueError('Error in datasets database: could not locate decision table pl_grow_sum')
		if pl_end_sum is None:
			raise ValueError('Error in datasets database: could not locate decision table pl_end_sum')
		if pl_grow_win is None:
			raise ValueError('Error in datasets database: could not locate decision table pl_grow_win')
		if pl_end_win is None:
			raise ValueError('Error in datasets database: could not locate decision table pl_end_win')

		hrus = []
		hru_cons = []
		cnt = get_max_id(gis.Gis_hrus)
		i = 1
		for row in gis.Gis_hrus.select():
			self.gis_to_hru_ids[row.id] = i
			plant = plants.get(row.landuse.lower())
			soil = hru_soils.get(row.soil)

			full_soil = soils.Soils_sol.get_or_none(soils.Soils_sol.name == row.soil)
			if full_soil is None:
				raise ValueError('Error in project database: could not locate soils_sol row named {}'.format(row.soil))
			slayer = full_soil.layers[0]

			soil_lte = self.get_soil_lte(slayer)

			urb = urbans.get(row.landuse.lower(), None)
			if urb is None:
				cn2 = self.get_cn2(soil_lte, row.landuse.lower())
				usle_k = slayer.usle_k
			else:
				cn2 = 98
				usle_k = slayer.soil_k * (1 - urb.frac_imp)

			hru_name = get_name('hru', row.id, cnt)
			slope = row.slope / 100
			slope_len = self.get_slope_len(row.slope)

			# Equation from Srini/Jeff email 3/6/19
			xm = 0.6 * (1 - math.exp(-35.835 * slope))
			sin_sl = math.sin(math.atan(slope))
			usle_ls = math.pow(slope_len / 22.128, xm) * (65.41 * sin_sl * sin_sl + 4.56 * sin_sl + .065)

			hru_data = {
				'id': i,
				'name': hru_name,
				'area': row.arslp,
				'cn2': cn2,
				'cn3_swf': 0,
				't_conc': 26,
				'soil_dp': full_soil.dp_tot,
				'perc_co': 0,
				'slp': slope,
				'slp_len': slope_len,
				'et_co': 1,
				'aqu_sp_yld': 0.05,
				'alpha_bf': 0.05,
				'revap': 0,
				'rchg_dp': 0.01,
				'sw_init': 0.5,
				'aqu_init': 3,
				'aqu_sh_flo': 0,
				'aqu_dp_flo': 300,
				'snow_h2o': 0,
				'lat': row.lat,
				'soil_text': soil_lte.id,
				'trop_flag': 'trop' if row.lat <= trop_bounds.north and row.lat >= trop_bounds.south else 'non_trop',
				'grow_start': pl_grow_win.id if plant.plnt_typ == 'cold_annual' else pl_grow_sum.id,
				'grow_end': pl_end_win.id if plant.plnt_typ == 'cold_annual' else pl_end_sum.id,
				'plnt_typ': plant.id,
				'stress': 0,
				'pet_flag': 'harg',
				'irr_flag': 'no_irr',
				'irr_src': 'outside_bsn',
				't_drain': 0,
				'usle_k': usle_k,
				'usle_c': plant.usle_c_min,
				'usle_p': 1,
				'usle_ls': usle_ls
			}
			hrus.append(hru_data)

			con = {
				'id': i,
				'lhru': i,
				'name': hru_name,
				'gis_id': row.id,
				'elev': row.elev,
				'lat': row.lat,
				'lon': row.lon,
				'area': row.arslp,
				'ovfl': 0,
				'rule': 0
			}
			hru_cons.append(con)

			i += 1
		
		db_lib.bulk_insert(self.project_db, hru.Hru_lte_hru, hrus)
		db_lib.bulk_insert(self.project_db, connect.Hru_lte_con, hru_cons)

	def get_slope_len(self, slope):
		if slope < 1:
			return 121
		elif slope < 3:
			return 90
		elif slope < 5:
			return 60
		elif slope < 8:
			return 30
		else:
			return 10

	def get_soil_lte(self, soil):
		name = 'sand'

		if 86 <= soil.sand <= 100 and 0 <= soil.silt <= 14 and 0 <= soil.clay <= 10:
			name = 'sand'
		elif 70 <= soil.sand <= 86 and 0 <= soil.silt <= 30 and 0 <= soil.clay <= 15:
			name = 'loamy_sand'
		elif 50 <= soil.sand <= 70 and 0 <= soil.silt <= 50 and 0 <= soil.clay <= 20:
			name = 'sandy_loam'
		elif 23 <= soil.sand <= 52 and 28 <= soil.silt <= 50 and 7 <= soil.clay <= 27:
			name = 'loam'
		elif 20 <= soil.sand <= 50 and 74 <= soil.silt <= 88 and 0 <= soil.clay <= 27:
			name = 'silt_loam'
		elif 0 <= soil.sand <= 20 and 88 <= soil.silt <= 100 and 0 <= soil.clay <= 12:
			name = 'silt'
		elif 20 <= soil.sand <= 45 and 15 <= soil.silt <= 52 and 27 <= soil.clay <= 40:
			name = 'clay_loam'
		elif 45 <= soil.sand <= 80 and 0 <= soil.silt <= 28 and 20 <= soil.clay <= 35:
			name = 'sandy_clay_loam'
		elif 0 <= soil.sand <= 20 and 40 <= soil.silt <= 73 and 27 <= soil.clay <= 40:
			name = 'silty_clay_loam'
		elif 45 <= soil.sand <= 65 and 0 <= soil.silt <= 20 and 35 <= soil.clay <= 55:
			name = 'sandy_clay'
		elif 0 <= soil.sand <= 20 and 40 <= soil.silt <= 60 and 40 <= soil.clay <= 60:
			name = 'silty_clay'
		elif 0 <= soil.sand <= 45 and 0 <= soil.silt <= 40 and 40 <= soil.clay <= 100:
			name = 'loamy_sand'

		return soils.Soils_lte_sol.get_or_none(soils.Soils_lte_sol.name == name)

	def get_cn2(self, soil, lu):
		lum_name = '{name}_lum'.format(name=lu)
		ds_m = ds_lum.Landuse_lum.get(ds_lum.Landuse_lum.name == lum_name)
		cntable = ds_m.cn2

		texture_map = {
			'sand': cntable.cn_a,
			'loamy_sand': cntable.cn_a,
			'sandy_loam': cntable.cn_b,
			'loam': cntable.cn_b,
			'silt_loam': cntable.cn_b,
			'silt': cntable.cn_c,
			'silty_clay_loam':  cntable.cn_c,
			'clay_loam': cntable.cn_d,
			'sandy_clay_loam': cntable.cn_c,
			'sandy_clay': cntable.cn_d,
			'silty_clay': cntable.cn_d,
			'clay': cntable.cn_d
		}

		return texture_map.get(soil.name, cntable.cn_a)

	def insert_connections(self, is_lte_cha_type=False):
		rtu_con_outs = self.get_connections([RouteCat.LSU], 'rtu_con', self.gis_to_rtu_ids, is_lte_cha_type=is_lte_cha_type)
		db_lib.bulk_insert(self.project_db, connect.Rout_unit_con_out, rtu_con_outs)

		attach_key = 'chandeg_con' if is_lte_cha_type else 'channel_con'
		con_out_table = connect.Chandeg_con_out if is_lte_cha_type else connect.Channel_con_out

		cha_con_outs = self.get_connections([RouteCat.CH], attach_key, self.gis_to_cha_ids, is_lte_cha_type=is_lte_cha_type)
		db_lib.bulk_insert(self.project_db, con_out_table, cha_con_outs)

		res_con_outs = self.get_connections([RouteCat.WTR, RouteCat.PND, RouteCat.RES], 'reservoir_con', self.gis_to_res_ids, is_lte_cha_type=is_lte_cha_type)
		db_lib.bulk_insert(self.project_db, connect.Reservoir_con_out, res_con_outs)

	def insert_connections_lte(self):
		cha_con_outs = self.get_connections([RouteCat.CH], 'chandeg_con', self.gis_to_cha_ids, True)
		db_lib.bulk_insert(self.project_db, connect.Chandeg_con_out, cha_con_outs)

		hru_con_outs = self.get_connections([RouteCat.HRU], 'hru_lte_con', self.gis_to_hru_ids, True, override_frac=True)
		db_lib.bulk_insert(self.project_db, connect.Hru_lte_con_out, hru_con_outs)

	def get_connections(self, sourcecats, attach_key, id_list, is_lte=False, override_frac=False, is_lte_cha_type=False):
		con_outs = []
		used = dict()
		for row in gis.Gis_routing.select().where((gis.Gis_routing.sourcecat << sourcecats) & (gis.Gis_routing.percent > 0)).order_by(gis.Gis_routing.sourceid):
			if row.sinkcat != RouteCat.OUTLET:
				id = id_list[row.sourceid]
				if id in used:
					used[id] += 1
				else:
					used[id] = 1

				if row.sourcecat == RouteCat.LSU and row.sinkcat == RouteCat.LSU:
					upland_lsu = gis.Gis_lsus.get_or_none(gis.Gis_lsus.id == row.sourceid)
					floodplain_lsu = gis.Gis_lsus.get_or_none(gis.Gis_lsus.id == row.sinkid)
					if upland_lsu is not None and floodplain_lsu is not None:
						upland_frac = upland_lsu.area / (upland_lsu.area + floodplain_lsu.area)
						floodplain_route = gis.Gis_routing.get_or_none((gis.Gis_routing.sourceid == row.sinkid) & (gis.Gis_routing.sourcecat == RouteCat.LSU))

						if floodplain_route is not None:
							ru_id = self.gis_to_rtu_ids[row.sinkid]

							if floodplain_route.sinkcat == RouteCat.CH:
								cha_id = self.gis_to_cha_ids[upland_lsu.channel]

								con_outs.append({
									'rtu_con': id,
									'order': 1,
									'obj_typ': 'sdc' if is_lte or is_lte_cha_type else 'cha',
									'obj_id': cha_id,
									'hyd_typ': 'sur',
									'frac': upland_frac
								})
								con_outs.append({
									'rtu_con': id,
									'order': 2,
									'obj_typ': 'aqu',
									'obj_id': self.gis_to_upland_aqu_ids[upland_lsu.channel],
									'hyd_typ': 'rhg',
									'frac': 1
								})						
								con_outs.append({
									'rtu_con': id,
									'order': 3,
									'obj_typ': 'ru',
									'obj_id': ru_id,
									'hyd_typ': 'sur',
									'frac': 1 - upland_frac
								})						
								con_outs.append({
									'rtu_con': id,
									'order': 4,
									'obj_typ': 'ru',
									'obj_id': ru_id,
									'hyd_typ': 'lat',
									'frac': 1
								})
							elif floodplain_route.sinkcat == RouteCat.WTR or floodplain_route.sinkcat == RouteCat.RES or floodplain_route.sinkcat == RouteCat.PND:
								res_id = self.gis_to_res_ids[floodplain_route.sinkid]
								res = gis.Gis_water.get_or_none(gis.Gis_water.id == floodplain_route.sinkid)

								if res is not None:
									res_cha = res.lsu // 10
									aqu_id = 0
									if res_cha in self.gis_to_upland_aqu_ids:
										aqu_id = self.gis_to_upland_aqu_ids[res_cha]
									elif res.subbasin in self.sub_to_upland_aqu_id:
										aqu_id = self.sub_to_upland_aqu_id[res.subbasin]
									else:
										aqu_id = self.sub_to_flood_aqu_id[res.subbasin]

									con_outs.append({
										'rtu_con': id,
										'order': 1,
										'obj_typ': 'res',
										'obj_id': res_id,
										'hyd_typ': 'sur',
										'frac': upland_frac
									})
									con_outs.append({
										'rtu_con': id,
										'order': 2,
										'obj_typ': 'aqu',
										'obj_id': aqu_id,
										'hyd_typ': 'rhg',
										'frac': 1
									})
									con_outs.append({
										'rtu_con': id,
										'order': 3,
										'obj_typ': 'ru',
										'obj_id': ru_id,
										'hyd_typ': 'sur',
										'frac': 1 - upland_frac
									})						
									con_outs.append({
										'rtu_con': id,
										'order': 4,
										'obj_typ': 'ru',
										'obj_id': ru_id,
										'hyd_typ': 'lat',
										'frac': 1
									})
				else:
					con_out = self.get_con_out(row.sinkid, row.sinkcat, row.percent, used[id], attach_key, id, is_lte, override_frac, is_lte_cha_type)
					if con_out is not None:
						con_outs.extend(con_out)

				if RouteCat.LSU in sourcecats and (row.sinkcat == RouteCat.CH or row.sinkcat == RouteCat.RES):
					used[id] += 1
					add_con_out = True
					if row.sinkcat == RouteCat.RES:
						res = gis.Gis_water.get_or_none(gis.Gis_water.id == row.sinkid)
						sub = res.subbasin
						if sub in self.sub_to_flood_aqu_id:
							aqu_id = self.sub_to_flood_aqu_id[sub]
						elif sub in self.sub_to_upland_aqu_id:
							aqu_id = self.sub_to_upland_aqu_id[sub]
						else:
							add_con_out = False
					else:
						use_cha = row.sinkid
						if use_cha in self.gis_to_flood_aqu_ids:
							aqu_id = self.gis_to_flood_aqu_ids[use_cha]
						elif use_cha in self.gis_to_upland_aqu_ids:
							aqu_id = self.gis_to_upland_aqu_ids[use_cha]
						else:
							add_con_out = False

					if add_con_out:
						aqu_con_out = {
							'rtu_con': id,
							'order': used[id],
							'obj_typ': 'aqu',
							'obj_id': aqu_id,
							'hyd_typ': 'rhg',
							'frac': 1
						}
						con_outs.append(aqu_con_out)

		return con_outs

	def get_con_out(self, sinkid, sinkcat, percent, order, attach_key, attach_id, is_lte=False, override_frac=False, is_lte_cha_type=False):
		if sinkcat == RouteCat.CH:
			con_out = {
				attach_key: attach_id,
				'order': order,
				'obj_typ': 'sdc' if is_lte or is_lte_cha_type else 'cha',
				'obj_id': self.gis_to_cha_ids[sinkid],
				'hyd_typ': 'tot',
				'frac': percent / 100 if not override_frac else 1
			}
			return [con_out]

		if not is_lte:
			if sinkcat == RouteCat.LSU:
				con_out = {
					attach_key: attach_id,
					'order': order,
					'obj_typ': 'ru',
					'obj_id': self.gis_to_rtu_ids[sinkid],
					'hyd_typ': 'tot',
					'frac': percent / 100
				}
				return [con_out]
			if sinkcat == RouteCat.WTR or sinkcat == RouteCat.RES or sinkcat == RouteCat.PND:
				con_out = {
					attach_key: attach_id,
					'order': order,
					'obj_typ': 'res',
					'obj_id': self.gis_to_res_ids[sinkid],
					'hyd_typ': 'tot',
					'frac': percent / 100
				}
				return [con_out]

		if sinkcat == RouteCat.PT:
			con_outs = []
			for row in gis.Gis_routing.select().where(
				(gis.Gis_routing.sourcecat == RouteCat.PT) & (gis.Gis_routing.sourceid == sinkid)):
				con_out = self.get_con_out(row.sinkid, row.sinkcat, row.percent, order, attach_key, attach_id, is_lte, is_lte_cha_type=is_lte_cha_type)
				if con_out is not None:
					con_outs.extend(con_out)
					order += 1

			return con_outs

		return None

	def insert_lsus(self):
		if connect.Hru_con.select().count() > 0:
			lsu_eles = []
			lsu_defs = []

			bsn_area = connect.Hru_con.select(fn.Sum(connect.Hru_con.area)).scalar()
			if bsn_area <= 0:
				raise ValueError('Project watershed area cannot be zero. Error summing HRU areas.')

			for row in connect.Rout_unit_con.select().order_by(connect.Rout_unit_con.id):
				if connect.Rout_unit_ele.select().where(connect.Rout_unit_ele.rtu_id == row.rtu.id).count() > 0:
					lsu_def = {
						'id': row.rtu.id,
						'name': row.name,
						'area': row.area
					}
					lsu_defs.append(lsu_def)

			db_lib.bulk_insert(self.project_db, regions.Ls_unit_def, lsu_defs)

			"""i = 1
			for row in connect.Hru_con.select().order_by(connect.Hru_con.id):
				try:
					ru_ele = connect.Rout_unit_ele.get((connect.Rout_unit_ele.obj_typ == 'hru') & (connect.Rout_unit_ele.obj_id == row.id))
					lsu_ele = {
						'id': i,
						'name': row.name,
						'obj_typ': 'hru',
						'obj_typ_no': row.id,
						'bsn_frac': row.area / bsn_area,
						'sub_frac': ru_ele.frac,
						'reg_frac': 0,
						'ls_unit_def': ru_ele.rtu.id
					}

					lsu_eles.append(lsu_ele)
					i += 1
				except connect.Rout_unit_ele.DoesNotExist:
					pass

			db_lib.bulk_insert(self.project_db, regions.Ls_unit_ele, lsu_eles)"""


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Import GIS tables into SWAT+ connection tables.")
	parser.add_argument("project_db_file", type=str, help="full path of project SQLite database file")
	parser.add_argument("delete_existing", type=str, help="y/n delete existing data first")
	args = parser.parse_args()

	del_ex = True if args.delete_existing == "y" else False

	gis_api = GisImport(args.project_db_file, del_ex)
	gis_api.insert_default()
