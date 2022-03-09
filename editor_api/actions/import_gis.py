#import logging
#logging.basicConfig(filename='swatplus_import_gis.log', filemode='w', level=logging.DEBUG)

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
from .import_gis_legacy import GisImport as GisImportLegacy

from peewee import *
from playhouse.shortcuts import model_to_dict
from playhouse.migrate import *

import sys, traceback
import argparse
import math

min_gis_version = 13


def is_supported_version(version):
	ver = version
	if len(ver) >= 3:
		ver = version[:3]

	ver = ver.replace('.', '')
	if int(ver) < min_gis_version:
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
	AQU = "AQU"
	DAQ = "DAQ"
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
		self.gis_to_aqu_ids = {}
		self.gis_to_deep_aqu_ids = {}

		if delete_existing and not self.config.imported_gis:
			self.delete_existing()

	def insert_default(self):
		if not is_supported_version(self.config.gis_version):
			legacy_api = GisImportLegacy(self.project_db_file, False, self.constant_ps, self.rollback_db)
			legacy_api.insert_default()
		elif not self.config.imported_gis:
			try:
				if gis.Gis_subbasins.select().count() > 0:					
					if self.is_lte:
						# self.emit_progress(15, "Importing channels from GIS...")
						self.insert_om_water()
						self.insert_channels_lte()

						# self.emit_progress(40, "Importing landscape units from GIS...")
						self.insert_lsus_lte()

						# self.emit_progress(50, "Importing hrus from GIS...")
						self.insert_hru_ltes()

						# self.emit_progress(90, "Importing connections from GIS...")
						self.insert_connections_lte()
					else:
						# self.emit_progress(15, "Importing routing units from GIS...")
						self.insert_routing_units()

						# self.emit_progress(30, "Importing channels from GIS...")
						self.insert_om_water()
						self.insert_channels_lte()

						# self.emit_progress(40, "Importing reservoirs from GIS...")
						self.insert_reservoirs()

						# self.emit_progress(50, "Importing point source from GIS...")
						self.insert_recall()

						# self.emit_progress(60, "Importing hrus from GIS...")
						self.insert_hrus()
						
						# self.emit_progress(75, "Importing aquifers from GIS...")
						self.insert_aquifers()

						# self.emit_progress(90, "Importing connections from GIS...")
						self.insert_connections()

						# self.emit_progress(95, "Creating default landscape units...")
						self.insert_lsus()

						if climate.Weather_sta_cli.select().count() > 0:
							w_api = WeatherImport(self.project_db_file, False, False)
							w_api.match_stations(70)

					config = Project_config.get()
					config.imported_gis = True
					config.save()
				else:
					# self.emit_progress(95, "No GIS data to import...")
					pass
			except Exception as err:
				#logging.debug("Import error encountered. Trying rollback: {}".format(self.rollback_db))
				if self.rollback_db is not None:
					# self.emit_progress(50, "Error occurred. Rolling back database...")
					SetupProjectDatabase.rollback(self.project_db_file, self.rollback_db)
					# self.emit_progress(100, "Error occurred.")
				sys.exit(traceback.format_exc())

	def delete_existing(self):
		# self.emit_progress(5, "Deleting existing connections before importing from GIS...")
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

					if (act.act_typ == 'plant' or act.act_typ == 'harvest_kill') and act.const2 == 0:
						act.const2 = 1
					elif act.act_typ == 'harvest_kill' and (act.fp == 'null' or act.fp == '' or act.fp is None):
						act.fp = 'grain'

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

				# Channel tables
				hyd_cha = {
					'id': i,
					'name': 'hyd%s' % cha_name,
					'order': str(row.strahler),
					'wd': row.wid2,
					'dp': row.dep2,
					'slp': row.slo2 / 100,
					'len': row.len2 / 1000,
					'mann': 0.05,
					'k': 1,
					'erod_fact': 0.01,
					'cov_fact': 0.005,
					'wd_rto': 4 if row.dep2 == 0 else row.wid2 / row.dep2,
					'eq_slp': 0.001,
					'd50': 12,
					'clay': 50,
					'carbon': 0.04,
					'dry_bd': 1,
					'side_slp': 0.5,
					'bed_load': 0.5,
					'fps': 0.00001,
					'fpn': 0.1,
					'n_conc': 0,
					'p_conc': 0,
					'p_bio': 0
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
					'lat': row.midlat,
					'lon': row.midlon,
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

	def insert_recall(self):
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
						'jday': 1,
						'mo': 1,
						'day_mo': 1,
						'yr': 1,
						'ob_typ': 'pt_const',
						'ob_name': rec_name,
						'flo': 0,
						'sed': 0,
						'orgn': 0,
						'sedp': 0,
						'no3': 0,
						'solp': 0,
						'chla': 0,
						'nh3': 0,
						'no2': 0,
						'cbod': 0,
						'dox': 0,
						'sand': 0,
						'silt': 0,
						'clay': 0,
						'sag': 0,
						'lag': 0,
						'gravel': 0,
						'tmp': 0
					}
					rec_data.append(data)

					con = gis.Gis_routing.get_or_none((gis.Gis_routing.sourcecat == RouteCat.PT) 
						& (gis.Gis_routing.sourceid == row.id)
						& (gis.Gis_routing.sinkcat == RouteCat.CH))

					if con is not None:
						rec_con_outs.append({
							'recall_con': i,
							'order': 1,
							'obj_typ': 'sdc',
							'obj_id': self.gis_to_cha_ids[con.sinkid],
							'hyd_typ': con.hyd_typ,
							'frac': con.percent / 100
						})

					i += 1

				db_lib.bulk_insert(self.project_db, connect.Recall_con, rec_cons)
				db_lib.bulk_insert(self.project_db, connect.Recall_con_out, rec_con_outs)
				db_lib.bulk_insert(self.project_db, recall.Recall_rec, recs)
				db_lib.bulk_insert(self.project_db, recall.Recall_dat, rec_data)

	def insert_landuse(self):
		"""
		Insert default plant.ini and landuse.lum for any plants and urbans that don't already have one.
		"""
		lum_default_cal_group = None
		lum_default_mgt = None
		lum_default_cn2 = 5
		lum_default_cons_prac = 1
		lum_default_ov_mann = 2

		distinct_lu = gis.Gis_hrus.select(gis.Gis_hrus.landuse).where((gis.Gis_hrus.landuse.is_null(False)) & (gis.Gis_hrus.landuse != 'NULL')).distinct()
		lus = [item.landuse.lower() for item in distinct_lu]
		for lu in lus:
			try:
				plant = hru_parm_db.Plants_plt.get(hru_parm_db.Plants_plt.name ** lu)
				p_id = plant.id

				lum_name = '{name}_lum'.format(name=lu)
				comm_name = '{name}_comm'.format(name=lu)
				try:
					pcom = None
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

					mgt_id = None
					new_d_table_id = None
					plant1 = None
					if plant.plnt_typ.startswith('warm_annual'):
						summer_table = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_hv_summer1')
						if summer_table is None:
							new_d_table_id = self.insert_d_table(plant.name, 'pl_hv_corn')
						else:
							new_d_table_id = summer_table.id
							plant1 = plant.name
					elif plant.plnt_typ.startswith('cold_annual'):
						winter_table = decision_table.D_table_dtl.get_or_none(decision_table.D_table_dtl.name == 'pl_hv_winter1')
						if winter_table is None:
							new_d_table_id = self.insert_d_table(plant.name, 'pl_hv_wwht')
						else:
							new_d_table_id = winter_table.id
							plant1 = plant.name

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
								d_table=new_d_table_id,
								plant1=plant1
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
			name = 'soilnut1',
			exp_co = 0.0005,
			lab_p = 5,
			nitrate = 7,
			fr_hum_act = 0.02,
			hum_c_n = 10,
			hum_c_p = 80,
			inorgp = 3.5,
			watersol_p = 0.15,
			h3a_p = 0.25,
			mehlich_p = 1.2,
			bray_strong_p = 0.85
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

			soil = soils.Soils_sol.get_or_none(soils.Soils_sol.name == row.soil)
			if soil is None:
				raise ValueError('Soil "{s}" does not exist in your soils_sol table. Check your project in GIS and make '
								 'sure all soils from the gis_hrus table exist in soils_sol.'.format(s=row.soil))

			hyd_calc = hydrology.Hydrology_hyd.get_perco_cn3_swf_latq_co(soil.hyd_grp, row.slope / 100)

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
				'cn3_swf': hyd_calc['cn3_swf'],
				'bio_mix': 0.20,
				'perco': hyd_calc['perco'],
				'lat_orgn': 0.00,
				'lat_orgp': 0.00,
				'harg_pet': 0.00,
				'latq_co': hyd_calc['latq_co']
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

			wetland_lu = ['wehb', 'wetf', 'wetl', 'wetn', 'wewo', 'watr', 'playa', 'wetw', 'wetm']

			lowercase_landuse = None if row.landuse is None else row.landuse.lower()

			if lowercase_landuse in wetland_lu:
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
				'lu_mgt': lum_dict.get(lowercase_landuse, None),
				'soil_plant_init': sp.id,
				'snow': 1,
				'surf_stor': wi-1 if lowercase_landuse in wetland_lu else None,
				'soil': soil.id
			}

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
		distinct_lu = gis.Gis_hrus.select(gis.Gis_hrus.landuse).where((gis.Gis_hrus.landuse.is_null(False)) & (gis.Gis_hrus.landuse != 'NULL')).distinct()
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
		lsu_eles = []
		bsn_area = gis.Gis_subbasins.select(fn.Sum(gis.Gis_subbasins.area)).scalar()
		cnt = get_max_id(gis.Gis_hrus)
		i = 1
		for row in gis.Gis_hrus.select():
			self.gis_to_hru_ids[row.id] = i
			lowercase_landuse = None if row.landuse is None else row.landuse.lower()

			plant = plants.get(lowercase_landuse, None)
			soil = hru_soils.get(row.soil)

			full_soil = soils.Soils_sol.get_or_none(soils.Soils_sol.name == row.soil)
			if full_soil is None:
				raise ValueError('Error in project database: could not locate soils_sol row named {}'.format(row.soil))
			slayer = full_soil.layers[0]

			soil_lte = self.get_soil_lte(slayer)

			urb = urbans.get(lowercase_landuse, None)
			if urb is None:
				cn2 = self.get_cn2(soil_lte, lowercase_landuse)
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
				'grow_start': pl_grow_win.id if plant is not None and plant.plnt_typ == 'cold_annual' else pl_grow_sum.id,
				'grow_end': pl_end_win.id if plant is not None and plant.plnt_typ == 'cold_annual' else pl_end_sum.id,
				'plnt_typ': None if plant is None else plant.id,
				'stress': 0,
				'pet_flag': 'harg',
				'irr_flag': 'no_irr',
				'irr_src': 'outside_bsn',
				't_drain': 0,
				'usle_k': usle_k,
				'usle_c': 0 if plant is None else plant.usle_c_min,
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

			lsu_ele = {
				'id': i,
				'name': hru_name,
				'obj_typ': 'hlt',
				'obj_typ_no': i,
				'bsn_frac': row.arslp / bsn_area,
				'sub_frac': row.arslp / row.arlsu,
				'reg_frac': 0,
				'ls_unit_def': self.gis_to_rtu_ids[row.lsu]
			}
			lsu_eles.append(lsu_ele)

			i += 1
		
		db_lib.bulk_insert(self.project_db, hru.Hru_lte_hru, hrus)
		db_lib.bulk_insert(self.project_db, connect.Hru_lte_con, hru_cons)
		db_lib.bulk_insert(self.project_db, regions.Ls_unit_ele, lsu_eles)

	def insert_aquifers(self):
		cnt = get_max_id(gis.Gis_aquifers)
		cnt_dp = get_max_id(gis.Gis_deep_aquifers)
		if aquifer.Aquifer_aqu.select().count() == 0:
			init_aqu = aquifer.Initial_aqu.create(
				name='initaqu1',
				org_min=1
			)

			aquifer_aqus = []
			aquifer_cons = []

			i = 1
			for row in gis.Gis_aquifers.select().order_by(gis.Gis_aquifers.id):
				self.gis_to_aqu_ids[row.id] = i

				aqu_name = get_name('aqu', row.id, cnt)
				aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_shallow(i, aqu_name, init_aqu.id))
				aqu_con = {
					'aqu': i,
					'id': i,
					'name': aqu_name,
					'gis_id': row.id,
					'lat': row.lat,
					'lon': row.lon,
					'area': row.area,
					'elev': row.elev,
					'ovfl': 0,
					'rule': 0
				}
				aquifer_cons.append(aqu_con)
				i += 1

			for row in gis.Gis_deep_aquifers.select().order_by(gis.Gis_deep_aquifers.id):
				self.gis_to_deep_aqu_ids[row.id] = i

				aqu_name = get_name('aqu_deep', row.id, cnt)
				aquifer_aqus.append(aquifer.Aquifer_aqu.get_default_deep(i, aqu_name, init_aqu.id))
				aqu_con = {
					'aqu': i,
					'id': i,
					'name': aqu_name,
					'gis_id': row.id,
					'lat': row.lat,
					'lon': row.lon,
					'area': row.area,
					'elev': row.elev,
					'ovfl': 0,
					'rule': 0
				}
				aquifer_cons.append(aqu_con)
				i += 1

			db_lib.bulk_insert(self.project_db, aquifer.Aquifer_aqu, aquifer_aqus)
			db_lib.bulk_insert(self.project_db, connect.Aquifer_con, aquifer_cons)

	def insert_connections(self):
		rtu_con_outs = self.get_connections([RouteCat.LSU], 'rtu_con', self.gis_to_rtu_ids)
		db_lib.bulk_insert(self.project_db, connect.Rout_unit_con_out, rtu_con_outs)

		cha_con_outs = self.get_connections([RouteCat.CH], 'chandeg_con', self.gis_to_cha_ids)
		db_lib.bulk_insert(self.project_db, connect.Chandeg_con_out, cha_con_outs)

		aqu_con_outs = self.get_connections([RouteCat.AQU], 'aquifer_con', self.gis_to_aqu_ids)
		db_lib.bulk_insert(self.project_db, connect.Aquifer_con_out, aqu_con_outs)

		res_con_outs = self.get_connections([RouteCat.WTR, RouteCat.PND, RouteCat.RES], 'reservoir_con', self.gis_to_res_ids)
		db_lib.bulk_insert(self.project_db, connect.Reservoir_con_out, res_con_outs)

	def insert_connections_lte(self):
		cha_con_outs = self.get_connections([RouteCat.CH], 'chandeg_con', self.gis_to_cha_ids, True)
		db_lib.bulk_insert(self.project_db, connect.Chandeg_con_out, cha_con_outs)

		# Send 100% HRU to channel
		hru_con_outs = []
		rows = gis.Gis_routing.select().where((gis.Gis_routing.sourcecat == RouteCat.HRU) 
				& (gis.Gis_routing.percent > 0) 
				& (gis.Gis_routing.sinkcat == RouteCat.CH)).order_by(gis.Gis_routing.sourceid)
		for row in rows:
			hru_con_outs.append({
				'hru_lte_con': self.gis_to_hru_ids[row.sourceid],
				'order': 1,
				'obj_typ': 'sdc',
				'obj_id': self.gis_to_cha_ids[row.sinkid],
				'hyd_typ': 'tot',
				'frac': 1
			})
		db_lib.bulk_insert(self.project_db, connect.Hru_lte_con_out, hru_con_outs)

	def get_connections(self, sourcecats, attach_key, id_list, is_lte=False):
		con_outs = []

		cats_to_obj_typ = {
			RouteCat.CH: 'sdc',
			RouteCat.AQU: 'aqu',
			RouteCat.DAQ: 'aqu',
			RouteCat.LSU: 'ru',
			RouteCat.WTR: 'res',
			RouteCat.RES: 'res',
			RouteCat.PND: 'res'
		}

		cats_to_list = {
			RouteCat.CH: self.gis_to_cha_ids,
			RouteCat.AQU: self.gis_to_aqu_ids,
			RouteCat.DAQ: self.gis_to_deep_aqu_ids,
			RouteCat.LSU: self.gis_to_rtu_ids,
			RouteCat.WTR: self.gis_to_res_ids,
			RouteCat.RES: self.gis_to_res_ids,
			RouteCat.PND: self.gis_to_res_ids
		}

		supported_sinkcats = [
			RouteCat.CH,
			RouteCat.AQU,
			RouteCat.DAQ,
			RouteCat.LSU,
			RouteCat.WTR,
			RouteCat.RES,
			RouteCat.PND
		]

		if is_lte:
			supported_sinkcats = [
				RouteCat.CH
			]

		rows = gis.Gis_routing.select().where((gis.Gis_routing.sourcecat << sourcecats) 
				& (gis.Gis_routing.percent > 0) 
				& (gis.Gis_routing.sinkcat != RouteCat.OUTLET)).order_by(gis.Gis_routing.sourceid)

		orders = dict()
		for row in rows:
			con_row = row
			while con_row.sinkcat == RouteCat.PT:
				con_row = gis.Gis_routing.get_or_none((gis.Gis_routing.sourcecat == RouteCat.PT) & (gis.Gis_routing.sourceid == con_row.sinkid))
			
			if con_row is not None and con_row.sinkcat in supported_sinkcats:
				id = id_list[row.sourceid]
				if id in orders:
					orders[id] += 1
				else:
					orders[id] = 1

				try:				
					con_outs.append({
						attach_key: id,
						'order': orders[id],
						'obj_typ': cats_to_obj_typ[con_row.sinkcat],
						'obj_id': cats_to_list[con_row.sinkcat][con_row.sinkid],
						'hyd_typ': con_row.hyd_typ,
						'frac': con_row.percent / 100
					})
				except KeyError as ke:
					raise KeyError('Check gis_routing. It is referencing a missing element. Key error id {}, con_row.sinkcat {}, con_row.sinkid {}. Error: {}'.format(id, con_row.sinkcat, con_row.sinkid, str(ke)))

		return con_outs

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

	def insert_lsus_lte(self):
		if gis.Gis_lsus.select().count() > 0:
			lsu_eles = []
			lsu_defs = []

			cnt = get_max_id(gis.Gis_lsus)
			i = 1
			for row in gis.Gis_lsus.select().order_by(gis.Gis_lsus.id):
				self.gis_to_rtu_ids[row.id] = i
				if gis.Gis_hrus.select().where(gis.Gis_hrus.lsu == row.id).count() > 0:
					lsu_def = {
						'id': i,
						'name': get_name('lsu', row.id, cnt),
						'area': row.area
					}
					lsu_defs.append(lsu_def)
					i += 1

			db_lib.bulk_insert(self.project_db, regions.Ls_unit_def, lsu_defs)


if __name__ == '__main__':
	sys.stdout = Unbuffered(sys.stdout)
	parser = argparse.ArgumentParser(description="Import GIS tables into SWAT+ connection tables.")
	parser.add_argument("project_db_file", type=str, help="full path of project SQLite database file")
	parser.add_argument("delete_existing", type=str, help="y/n delete existing data first")
	args = parser.parse_args()

	del_ex = True if args.delete_existing == "y" else False

	gis_api = GisImport(args.project_db_file, del_ex)
	gis_api.insert_default()
