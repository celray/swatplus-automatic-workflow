from flask_restful import Resource, abort

from database.project.setup import SetupProjectDatabase
from database.project import connect, climate, channel, aquifer, reservoir, hydrology, hru, hru_parm_db, lum, soils, routing_unit, dr, init, decision_table, exco, dr, structural
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
