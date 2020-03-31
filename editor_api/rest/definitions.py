from flask_restful import Resource, abort
from playhouse.shortcuts import model_to_dict

from database.datasets.setup import SetupDatasetsDatabase
from database.vardefs import Var_range, Var_code


class VarRangeApi(Resource):
	def get(self, db, table):
		SetupDatasetsDatabase.init(db)
		m = Var_range.select().where(Var_range.table == table)
		
		values = {}
		for v in m:
			options = []
			for o in v.options:
				if o.text_only:
					options.append({'value': o.text, 'text': o.text})
				elif o.text_value is not None:
					options.append({'value': o.text_value, 'text': o.text})
				else:
					options.append({'value': o.value, 'text': o.text})

			values[v.variable] = {
				'name': v.variable,
				'type': v.type,
				'min_value': v.min_value,
				'max_value': v.max_value,
				'default_value': v.default_value,
				'default_text': v.default_text,
				'units': v.units,
				'description': v.description,
				'options': options #[model_to_dict(o, recurse=False) for o in v.options]
			}
			
		return values


class VarCodeApi(Resource):
	def get(self, db, table, variable):
		SetupDatasetsDatabase.init(db)
		m = Var_code.select().where((Var_code.table == table) & (Var_code.variable == variable))
		
		values = []
		for v in m:
			values.append({
				'value': v.code,
				'text': '{code} - {description}'.format(code=v.code, description=v.description)
			})
		
		return values
