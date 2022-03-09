from flask_restful import Resource, reqparse, abort

from database.project.setup import SetupProjectDatabase
from database.project import connect, climate, channel, aquifer, reservoir, hydrology, hru, hru_parm_db, lum, soils, routing_unit, dr, init, decision_table, exco, dr, structural, gis
from helpers import table_mapper # Note: string to table name dictionary moved here

MAX_ROWS = 10000


class AutoCompleteApi(Resource):
	def get(self, project_db, type, partial_name):
		SetupProjectDatabase.init(project_db)
		table = table_mapper.types.get(type, None)

		if table is None:
			return abort(404, message='Unable to find table type for auto-complete.')

		# If table is a decision table, filter based on file_name
		if '.dtl' in type:
			m = table.select(table.name).where((table.name.contains(partial_name)) & (table.file_name == type)).limit(MAX_ROWS)
			nm = table.select(table.name).where((~(table.name.contains(partial_name))) & (table.file_name == type)).limit(MAX_ROWS)
		else:
			m = table.select(table.name).where(table.name.contains(partial_name)).limit(MAX_ROWS)
			nm = table.select(table.name).where(~(table.name.contains(partial_name))).limit(MAX_ROWS)

		matches = [v.name for v in m]
		non_matches = [nv.name for nv in nm]
		
		if len(matches) > 0:
			if len(non_matches) > 0:
				return matches + non_matches
			return matches
		return non_matches


class AutoCompleteNoParmApi(Resource):
	def get(self, project_db, type):
		SetupProjectDatabase.init(project_db)
		table = table_mapper.types.get(type, None)

		if table is None:
			return abort(404, message='Unable to find table type for auto-complete.')

		# If table is a decision table, filter based on file_name
		if '.dtl' in type:
			m = table.select(table.name).where(table.file_name == type).order_by(table.name).limit(MAX_ROWS)
		else:
			m = table.select(table.name).order_by(table.name).limit(MAX_ROWS)

		return [v.name for v in m]


class AutoCompleteIdApi(Resource):
	def get(self, project_db, type, name):
		SetupProjectDatabase.init(project_db)
		table = table_mapper.types.get(type, None)

		if table is None:
			return abort(404, message='Unable to find table type for auto-complete.')

		try:
			m = table.get(table.name == name)
			return {'id': m.id}
		except table.DoesNotExist:
			abort(404, message='{name} does not exist in the database.'.format(name=name))


class SelectListApi(Resource):
	def get(self, project_db, type):
		SetupProjectDatabase.init(project_db)
		table = table_mapper.types.get(type, None)

		if table is None:
			return abort(404, message='Unable to find table type for auto-complete.')

		items = table.select().order_by(table.name)
		return [{'value': m.id, 'text': m.name} for m in items]


class SubbasinsListApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		items = gis.Gis_subbasins.select().order_by(gis.Gis_subbasins.id)
		return [{'value': m.id, 'text': 'Subbasin {}'.format(m.id)} for m in items]


class LanduseListApi(Resource):
	def post(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('selected_subs', type=list, required=True, location='json')
		args = parser.parse_args(strict=False)

		SetupProjectDatabase.init(project_db)
		selected_subs = args['selected_subs']
		chas = gis.Gis_channels.select(gis.Gis_channels.id).where(gis.Gis_channels.subbasin.in_(selected_subs))
		lsus = gis.Gis_lsus.select(gis.Gis_lsus.id).where(gis.Gis_lsus.channel.in_(chas))
		items = gis.Gis_hrus.select(gis.Gis_hrus.landuse).distinct().where(gis.Gis_hrus.lsu.in_(lsus))
		return [{'value': m.landuse, 'text': m.landuse} for m in items]


class SoilListApi(Resource):
	def post(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('selected_subs', type=list, required=True, location='json')
		parser.add_argument('selected_landuse', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		SetupProjectDatabase.init(project_db)
		selected_subs = args['selected_subs']
		selected_landuse = args['selected_landuse']
		chas = gis.Gis_channels.select(gis.Gis_channels.id).where(gis.Gis_channels.subbasin.in_(selected_subs))
		lsus = gis.Gis_lsus.select(gis.Gis_lsus.id).where(gis.Gis_lsus.channel.in_(chas))
		items = gis.Gis_hrus.select(gis.Gis_hrus.soil).distinct().where((gis.Gis_hrus.lsu.in_(lsus)) & (gis.Gis_hrus.landuse.in_(selected_landuse)))
		return [{'value': m.soil, 'text': m.soil} for m in items]


class MatchingObjectsListApi(Resource):
	def post(self, project_db, type):
		parser = reqparse.RequestParser()
		parser.add_argument('selected_subs', type=list, required=False, location='json')
		parser.add_argument('selected_landuse', type=list, required=False, location='json')
		parser.add_argument('selected_soils', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		SetupProjectDatabase.init(project_db)
		table = table_mapper.types.get(type, None)

		if table is None:
			return abort(404, message='Invalid connection table name provided.')

		items = table.select(table.id, table.name)

		if args['selected_subs'] is not None and len(args['selected_subs']) > 0:
			con_to_gis = {
				"aqu_con": gis.Gis_aquifers,
				"init_aqu": gis.Gis_aquifers,

				"res_con": gis.Gis_water,
				"init_res": gis.Gis_water,
				"hyd_res": gis.Gis_water,
				"sed_res": gis.Gis_water,
				"nut_res": gis.Gis_water,

				"rtu_con": gis.Gis_lsus,
				"fld": gis.Gis_lsus,
				"topo": gis.Gis_lsus,

				"hru_con": gis.Gis_hrus,
				"hru_lte_con": gis.Gis_hrus,
				"hyd": gis.Gis_hrus,
				"topo_hru": gis.Gis_hrus,
				"wet_res": gis.Gis_hrus,

				"chandeg_con": gis.Gis_channels,
				"init_cha": gis.Gis_channels,
				"hyd_sed_lte_cha": gis.Gis_channels,
				"nut_cha": gis.Gis_channels,

				"rec_con": gis.Gis_points
			}

			hru_types = ['rtu_con', 'hru_con', 'hru_lte_con', 'hyd', 'topo_hru', 'wet_res']
			rtu_types = ['rtu_con', 'fld', 'topo']

			gis_table = con_to_gis.get(type, None)
			if gis_table is None:
				return abort(404, message='Could not find matching GIS table.')
			
			prop_data = {
				"init_cha": (connect.Chandeg_con, channel.Channel_lte_cha, channel.Channel_lte_cha.init_id),
				"hyd_sed_lte_cha": (connect.Chandeg_con, channel.Channel_lte_cha, channel.Channel_lte_cha.hyd_id),
				"nut_cha": (connect.Chandeg_con, channel.Channel_lte_cha, channel.Channel_lte_cha.nut_id),

				"fld": (connect.Rout_unit_con, routing_unit.Rout_unit_rtu, routing_unit.Rout_unit_rtu.field_id),
				"topo": (connect.Rout_unit_con, routing_unit.Rout_unit_rtu, routing_unit.Rout_unit_rtu.topo_id),

				"hyd": (connect.Hru_con, hru.Hru_data_hru, hru.Hru_data_hru.hydro_id),
				"topo_hru": (connect.Hru_con, hru.Hru_data_hru, hru.Hru_data_hru.topo_id),
				"wet_res": (connect.Hru_con, hru.Hru_data_hru, hru.Hru_data_hru.surf_stor_id),

				"init_aqu": (connect.Aquifer_con, aquifer.Aquifer_aqu, aquifer.Aquifer_aqu.init_id),

				"init_res": (connect.Reservoir_con, reservoir.Reservoir_res, reservoir.Reservoir_res.init_id),
				"hyd_res": (connect.Reservoir_con, reservoir.Reservoir_res, reservoir.Reservoir_res.hyd_id),
				"sed_res": (connect.Reservoir_con, reservoir.Reservoir_res, reservoir.Reservoir_res.sed_id),
				"nut_res": (connect.Reservoir_con, reservoir.Reservoir_res, reservoir.Reservoir_res.nut_id)
			}
			prop_types = prop_data.get(type, None)

			selected_subs = args['selected_subs']

			if type in hru_types or type in rtu_types:
				chas = gis.Gis_channels.select(gis.Gis_channels.id).where(gis.Gis_channels.subbasin.in_(selected_subs))
				lsus = gis.Gis_lsus.select(gis.Gis_lsus.id).where(gis.Gis_lsus.channel.in_(chas))
				if type in hru_types:
					w = (gis.Gis_hrus.lsu.in_(lsus))
					if args['selected_landuse'] is not None and len(args['selected_landuse']) > 0:
						w = w & (gis.Gis_hrus.landuse.in_(args['selected_landuse']))
						if args['selected_soils'] is not None and len(args['selected_soils']) > 0:
							w = w & (gis.Gis_hrus.soil.in_(args['selected_soils']))
					sub_items = gis.Gis_hrus.select(gis.Gis_hrus.id).where(w)
					#items = items.where(table.gis_id.in_(hrus))
				else:
					sub_items = lsus
					#items = items.where(table.gis_id.in_(lsus))
			else:
				sub_items = gis_table.select(gis_table.id).where(gis_table.subbasin.in_(selected_subs))

			if prop_types is None:
				items = items.where(table.gis_id.in_(sub_items))
			else:
				con_table = prop_types[0]
				prop_table = prop_types[1]
				prop_col = prop_types[2]

				con_items = con_table.select(prop_col).join(prop_table).where(con_table.gis_id.in_(sub_items))
				items = items.where(table.id.in_(con_items))

		
		return [{'value': m.id, 'text': m.name} for m in items.order_by(table.name)]

