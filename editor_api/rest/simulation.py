from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict

from database.project.setup import SetupProjectDatabase
from database.project.simulation import Time_sim, Print_prt, Print_prt_object


class TimeSimApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		m = Time_sim.get_or_create_default()
		return model_to_dict(m)

	def put(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('day_start', type=int, required=True, location='json')
		parser.add_argument('yrc_start', type=int, required=True, location='json')
		parser.add_argument('day_end', type=int, required=True, location='json')
		parser.add_argument('yrc_end', type=int, required=True, location='json')
		parser.add_argument('step', type=int, required=False, location='json')
		args = parser.parse_args(strict=True)

		SetupProjectDatabase.init(project_db)
		result = Time_sim.update_and_exec(args['day_start'], args['yrc_start'], args['day_end'], args['yrc_end'], args['step'])

		if result == 1:
			return 200

		abort(400, message='Unable to update time_sim table.')


class PrintPrtApi(Resource):
	def get(self, project_db):
		SetupProjectDatabase.init(project_db)
		try:
			m = Print_prt.get()
			prt = model_to_dict(m, recurse=False)

			o = Print_prt_object.select()
			objects = [model_to_dict(v, recurse=False) for v in o]

			return {"prt": prt, "objects": objects}
		except Print_prt.DoesNotExist:
			abort(404, message="Could not retrieve print_prt data.")

	def put(self, project_db):
		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('nyskip', type=int, required=True, location='json')
		parser.add_argument('day_start', type=int, required=True, location='json')
		parser.add_argument('day_end', type=int, required=True, location='json')
		parser.add_argument('yrc_start', type=int, required=True, location='json')
		parser.add_argument('yrc_end', type=int, required=True, location='json')
		parser.add_argument('interval', type=int, required=True, location='json')
		parser.add_argument('csvout', type=bool, required=True, location='json')
		parser.add_argument('dbout', type=bool, required=True, location='json')
		parser.add_argument('cdfout', type=bool, required=True, location='json')
		parser.add_argument('soilout', type=bool, required=True, location='json')
		parser.add_argument('mgtout', type=bool, required=True, location='json')
		parser.add_argument('hydcon', type=bool, required=True, location='json')
		parser.add_argument('fdcout', type=bool, required=True, location='json')
		parser.add_argument('objects', type=list, required=False, location='json')
		args = parser.parse_args(strict=False)

		SetupProjectDatabase.init(project_db)
		q = Print_prt.update(
			nyskip=args['nyskip'],
			day_start=args['day_start'],
			day_end=args['day_end'],
			yrc_start=args['yrc_start'],
			yrc_end=args['yrc_end'],
			interval=args['interval'],
			csvout=args['csvout'],
			dbout=args['dbout'],
			cdfout=args['cdfout'],
			soilout=args['soilout'],
			mgtout=args['mgtout'],
			hydcon=args['hydcon'],
			fdcout=args['fdcout']
		)
		result = q.execute()

		if args['objects'] is not None:
			for o in args['objects']:
				Print_prt_object.update(
					daily=o['daily'],
					monthly=o['monthly'],
					yearly=o['yearly'],
					avann=o['avann']
				).where(Print_prt_object.id == o['id']).execute()

		return 200


class PrintPrtObjectApi(Resource):
	def put(self, project_db, id):
		parser = reqparse.RequestParser()
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('print_prt', type=int, required=True, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('daily', type=bool, required=True, location='json')
		parser.add_argument('monthly', type=bool, required=True, location='json')
		parser.add_argument('yearly', type=bool, required=True, location='json')
		parser.add_argument('avann', type=bool, required=True, location='json')
		args = parser.parse_args(strict=True)

		SetupProjectDatabase.init(project_db)
		q = Print_prt_object.update(
			daily=args['daily'],
			monthly=args['monthly'],
			yearly=args['yearly'],
			avann=args['avann']
		).where(Print_prt_object.id == id)
		result = q.execute()

		if result == 1:
			return 200

		abort(400, message='Unable to update print_print_object {}.'.format(args['name']))
