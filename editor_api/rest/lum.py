from flask_restful import Resource, reqparse, abort
from playhouse.shortcuts import model_to_dict
from peewee import *

from .base import BaseRestModel
from database.project import base
from database.project.setup import SetupProjectDatabase
from database.project.lum import Landuse_lum, Management_sch, Cntable_lum, Cons_prac_lum, Ovn_table_lum, Management_sch_auto, Management_sch_op
from database.project.structural import Tiledrain_str, Septic_str, Filterstrip_str, Grassedww_str, Bmpuser_str
from database.project.hru_parm_db import Urban_urb
from database.project.init import Plant_ini
from database.project.decision_table import D_table_dtl
from database.datasets.setup import SetupDatasetsDatabase
from database.datasets import lum as ds_lum
from database import lib
from helpers import utils

invalid_name_msg = 'Invalid name {name}. Please ensure the value exists in your database.'


def get_landuse_args(get_selected_ids=False):
	parser = reqparse.RequestParser()

	if get_selected_ids:
		parser.add_argument('selected_ids', type=int, action='append', required=False, location='json')
	else:
		parser.add_argument('id', type=int, required=False, location='json')
		parser.add_argument('name', type=str, required=True, location='json')
		parser.add_argument('description', type=str, required=False, location='json')

	parser.add_argument('cal_group', type=str, required=False, location='json')
	parser.add_argument('urb_ro', type=str, required=False, location='json')

	parser.add_argument('plnt_com_name', type=str, required=False, location='json')
	parser.add_argument('mgt_name', type=str, required=False, location='json')
	parser.add_argument('cn2_name', type=str, required=False, location='json')
	parser.add_argument('cons_prac_name', type=str, required=False, location='json')
	parser.add_argument('urban_name', type=str, required=False, location='json')
	parser.add_argument('ov_mann_name', type=str, required=False, location='json')
	parser.add_argument('tile_name', type=str, required=False, location='json')
	parser.add_argument('sep_name', type=str, required=False, location='json')
	parser.add_argument('vfs_name', type=str, required=False, location='json')
	parser.add_argument('grww_name', type=str, required=False, location='json')
	parser.add_argument('bmp_name', type=str, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args

def save_landuse_args(self, m, args):
	m.name = args['name']
	m.description = args['description']
	m.cal_group = utils.remove_space(args['cal_group'])
	m.urb_ro = args['urb_ro']

	m.plnt_com_id = self.get_id_from_name(Plant_ini, args['plnt_com_name'])
	m.mgt_id = self.get_id_from_name(Management_sch, args['mgt_name'])
	m.cn2_id = self.get_id_from_name(Cntable_lum, args['cn2_name'])
	m.cons_prac_id = self.get_id_from_name(Cons_prac_lum, args['cons_prac_name'])
	m.urban_id = self.get_id_from_name(Urban_urb, args['urban_name'])
	m.ov_mann_id = self.get_id_from_name(Ovn_table_lum, args['ov_mann_name'])
	m.tile_id = self.get_id_from_name(Tiledrain_str, args['tile_name'])
	m.sep_id = self.get_id_from_name(Septic_str, args['sep_name'])
	m.vfs_id = self.get_id_from_name(Filterstrip_str, args['vfs_name'])
	m.grww_id = self.get_id_from_name(Grassedww_str, args['grww_name'])
	m.bmp_id = self.get_id_from_name(Bmpuser_str, args['bmp_name'])

	return m.save()


class LanduseLumListApi(BaseRestModel):
	def get(self, project_db):
		table = Landuse_lum
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols, back_refs=True)


class LanduseLumApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Landuse_lum, 'Landuse', True)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Landuse_lum, 'Landuse')

	def put(self, project_db, id):
		args = get_landuse_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Landuse_lum.get(Landuse_lum.id == id)
			result = save_landuse_args(self, m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update land use properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Land use name must be unique.')
		except Landuse_lum.DoesNotExist:
			abort(404, message='Land use properties {id} does not exist'.format(id=id))
		except Plant_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['plnt_com_name']))
		except Management_sch.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['mgt_name']))
		except Cntable_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cn2_name']))
		except Cons_prac_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cons_prac_name']))
		except Urban_urb.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['urban_name']))
		except Ovn_table_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['ov_mann_name']))
		except Tiledrain_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['tile_name']))
		except Septic_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sep_name']))
		except Filterstrip_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['vfs_name']))
		except Grassedww_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['grww_name']))
		except Bmpuser_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['bmp_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class LanduseLumPostApi(BaseRestModel):
	def post(self, project_db):
		args = get_landuse_args()
		try:
			SetupProjectDatabase.init(project_db)

			m = Landuse_lum()
			result = save_landuse_args(self, m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update channel properties {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Channel properties name must be unique.')
		except Plant_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['plnt_com_name']))
		except Management_sch.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['mgt_name']))
		except Cntable_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cn2_name']))
		except Cons_prac_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cons_prac_name']))
		except Urban_urb.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['urban_name']))
		except Ovn_table_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['ov_mann_name']))
		except Tiledrain_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['tile_name']))
		except Septic_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sep_name']))
		except Filterstrip_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['vfs_name']))
		except Grassedww_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['grww_name']))
		except Bmpuser_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['bmp_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class LanduseLumUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Landuse_lum)

	def put(self, project_db):
		SetupProjectDatabase.init(project_db)
		args = get_landuse_args(True)
		
		try:
			param_dict = {}

			if args['cal_group'] is not None:
				param_dict['cal_group'] = utils.remove_space(args['cal_group'])
			if args['urb_ro'] is not None:
				param_dict['urb_ro'] = args['urb_ro']
			
			if args['plnt_com_name'] is not None:
				param_dict['plnt_com_id'] = self.get_id_from_name(Plant_ini, args['plnt_com_name'])
			if args['mgt_name'] is not None:
				param_dict['mgt_id'] = self.get_id_from_name(Management_sch, args['mgt_name'])
			if args['cn2_name'] is not None:
				param_dict['cn2_id'] = self.get_id_from_name(Cntable_lum, args['cn2_name'])
			if args['cons_prac_name'] is not None:
				param_dict['cons_prac_id'] = self.get_id_from_name(Cons_prac_lum, args['cons_prac_name'])
			if args['urban_name'] is not None:
				param_dict['urban_id'] = self.get_id_from_name(Urban_urb, args['urban_name'])
			if args['ov_mann_name'] is not None:
				param_dict['ov_mann_id'] = self.get_id_from_name(Ovn_table_lum, args['ov_mann_name'])
			if args['tile_name'] is not None:
				param_dict['tile_id'] = self.get_id_from_name(Tiledrain_str, args['tile_name'])
			if args['sep_name'] is not None:
				param_dict['sep_id'] = self.get_id_from_name(Septic_str, args['sep_name'])
			if args['vfs_name'] is not None:
				param_dict['vfs_id'] = self.get_id_from_name(Filterstrip_str, args['vfs_name'])
			if args['grww_name'] is not None:
				param_dict['grww_id'] = self.get_id_from_name(Grassedww_str, args['grww_name'])
			if args['bmp_name'] is not None:
				param_dict['bmp_id'] = self.get_id_from_name(Bmpuser_str, args['bmp_name'])

			query = Landuse_lum.update(param_dict).where(Landuse_lum.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update channel properties.')
		except Plant_ini.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['plnt_com_name']))
		except Management_sch.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['mgt_name']))
		except Cntable_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cn2_name']))
		except Cons_prac_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['cons_prac_name']))
		except Urban_urb.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['urban_name']))
		except Ovn_table_lum.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['ov_mann_name']))
		except Tiledrain_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['tile_name']))
		except Septic_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['sep_name']))
		except Filterstrip_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['vfs_name']))
		except Grassedww_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['grww_name']))
		except Bmpuser_str.DoesNotExist:
			abort(400, message=invalid_name_msg.format(name=args['bmp_name']))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


def save_cntable_lum(m, args):
	m.name = args['name']
	m.description = utils.remove_space(args['description'])
	m.cn_a = args['cn_a']
	m.cn_b = args['cn_b']
	m.cn_c = args['cn_c']
	m.cn_d = args['cn_d']
	m.treat = utils.remove_space(args['treat'])
	m.cond_cov = utils.remove_space(args['cond_cov'])
	return m.save()


class CntableLumListApi(BaseRestModel):
	def get(self, project_db):
		table = Cntable_lum
		filter_cols = [table.name, table.description, table.treat, table.cond_cov]
		return self.base_paged_list(project_db, table, filter_cols)


class CntableLumApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Cntable_lum, 'Curve Number')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Cntable_lum, 'Curve Number')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('cntable_lum', project_db)

			m = Cntable_lum.get(Cntable_lum.id == id)
			result = save_cntable_lum(m, args)

			if result > 0:
				return 200

			abort(400, message='Unable to update curve number table {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Curve number table name must be unique.')
		except Cntable_lum.DoesNotExist:
			abort(404, message='Curve number table {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CntableLumUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Cntable_lum)

	def put(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('cntable_lum', project_db, True)

			remove_spaces = ['description', 'treat', 'cond_cov']

			param_dict = {}
			for key in args.keys():
				if args[key] is not None and key != 'selected_ids':
					param_dict[key] = utils.remove_space(args[key]) if key in remove_spaces else args[key]

			query = Cntable_lum.update(param_dict).where(Cntable_lum.id.in_(args['selected_ids']))
			result = query.execute()

			if result > 0:
				return 200

			abort(400, message='Unable to update curve number tables.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CntableLumPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			SetupProjectDatabase.init(project_db)
			args = self.get_args('cntable_lum', project_db)

			m = Cntable_lum()
			result = save_cntable_lum(m, args)

			if result > 0:
				return model_to_dict(m), 201

			abort(400, message='Unable to update curve number table {id}.'.format(id=id))
		except IntegrityError as e:
			abort(400, message='Curve number table name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class CntableLumDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds_lum.Cntable_lum, 'Curve number table')


class OvntableLumListApi(BaseRestModel):
	def get(self, project_db):
		table = Ovn_table_lum
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class OvntableLumApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Ovn_table_lum, 'Mannings n')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Ovn_table_lum, 'Mannings n')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Ovn_table_lum, 'Mannings n')


class OvntableLumUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Ovn_table_lum)

	def put(self, project_db):
		return self.base_put_many(project_db, Ovn_table_lum, 'Mannings n')


class OvntableLumPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Ovn_table_lum, 'Mannings n')


class OvntableLumDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds_lum.Ovn_table_lum, 'Mannings n table')


class ConsPracLumListApi(BaseRestModel):
	def get(self, project_db):
		table = Cons_prac_lum
		filter_cols = [table.name, table.description]
		return self.base_paged_list(project_db, table, filter_cols)


class ConsPracLumApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Cons_prac_lum, 'Conservation practice')

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Cons_prac_lum, 'Conservation practice')

	def put(self, project_db, id):
		return self.base_put(project_db, id, Cons_prac_lum, 'Conservation practice')


class ConsPracLumUpdateManyApi(BaseRestModel):
	def get(self, project_db):
		return self.base_name_id_list(project_db, Cons_prac_lum)

	def put(self, project_db):
		return self.base_put_many(project_db, Cons_prac_lum, 'Conservation practice')


class ConsPracLumPostApi(BaseRestModel):
	def post(self, project_db):
		return self.base_post(project_db, Cons_prac_lum, 'Conservation practice')


class ConsPracLumDatasetsApi(BaseRestModel):
	def get(self, datasets_db, name):
		return self.base_get_datasets_name(datasets_db, name, ds_lum.Cons_prac_lum, 'Conservation practices')


def get_mgt_args():
	parser = reqparse.RequestParser()

	parser.add_argument('id', type=int, required=False, location='json')
	parser.add_argument('name', type=str, required=True, location='json')
	parser.add_argument('auto_ops', type=list, required=False, location='json')
	parser.add_argument('operations', type=list, required=False, location='json')
	args = parser.parse_args(strict=True)
	return args


class ManagementSchListApi(BaseRestModel):
	def get(self, project_db):
		table = Management_sch
		filter_cols = [table.name]
		
		items = self.base_paged_items(project_db, table, filter_cols)
		m = items['model']
		ml = [{'id': v.id, 'name': v.name, 'num_ops': len(v.operations), 'num_auto': len(v.auto_ops)} for v in m]

		return {
			'total': items['total'],
			'matches': items['matches'],
			'items': ml
		}


class ManagementSchApi(BaseRestModel):
	def get(self, project_db, id):
		return self.base_get(project_db, id, Management_sch, 'Management schedule', back_refs=True, max_depth=2)

	def delete(self, project_db, id):
		return self.base_delete(project_db, id, Management_sch, 'Management schedule')

	def put(self, project_db, id):
		try:
			SetupProjectDatabase.init(project_db)
			args = get_mgt_args()

			m = Management_sch.get(Management_sch.id == id)
			m.name = args['name']
			m.save()

			new_auto = []
			for a in args['auto_ops']:
				try:
					dt = D_table_dtl.get((D_table_dtl.file_name == 'lum.dtl') & (D_table_dtl.name == a['name']))
					new_auto.append({'management_sch_id': m.id, 'd_table_id': dt.id, 'plant1': a['plant1'], 'plant2': a['plant2']})
				except D_table_dtl.DoesNotExist:
					abort(404, message='Decision table {name} does not exist'.format(name=a['name']))

			new_ops = []
			order = 1
			for o in args['operations']:
				new_ops.append({
					'management_sch_id': m.id,
					'op_typ': o['op_typ'],
					'mon': o['mon'],
					'day': o['day'],
					'op_data1': o['op_data1'],
					'op_data2': o['op_data2'],
					'op_data3': o['op_data3'],
					'order': o['order'],
					'hu_sch': o['hu_sch']
				})
				order += 1

			Management_sch_auto.delete().where(Management_sch_auto.management_sch_id == m.id).execute()
			lib.bulk_insert(base.db, Management_sch_auto, new_auto)

			Management_sch_op.delete().where(Management_sch_op.management_sch_id == m.id).execute()
			lib.bulk_insert(base.db, Management_sch_op, new_ops)

			return 200
		except IntegrityError as e:
			abort(400, message='Management schedule name must be unique.')
		except Cons_prac_lum.DoesNotExist:
			abort(404, message='Management schedule {id} does not exist'.format(id=id))
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))


class ManagementSchPostApi(BaseRestModel):
	def post(self, project_db):
		try:
			args = get_mgt_args()

			m = Management_sch()
			m.name = args['name']
			m.save()

			new_auto = []
			for a in args['auto_ops']:
				try:
					dt = D_table_dtl.get((D_table_dtl.file_name == 'lum.dtl') & (D_table_dtl.name == a['name']))
					new_auto.append({'management_sch_id': m.id, 'd_table_id': dt.id, 'plant1': a['plant1'], 'plant2': a['plant2']})
				except D_table_dtl.DoesNotExist:
					abort(404, message='Decision table {name} does not exist'.format(name=a['name']))

			new_ops = []
			order = 1
			for o in args['operations']:
				new_ops.append({
					'management_sch_id': m.id,
					'op_typ': o['op_typ'],
					'mon': o['mon'],
					'day': o['day'],
					'op_data1': o['op_data1'],
					'op_data2': o['op_data2'],
					'op_data3': o['op_data3'],
					'order': o['order'],
					'hu_sch': o['hu_sch']
				})
				order += 1

			lib.bulk_insert(base.db, Management_sch_auto, new_auto)
			lib.bulk_insert(base.db, Management_sch_op, new_ops)

			return 201
		except IntegrityError as e:
			abort(400, message='Management schedule name must be unique.')
		except Exception as ex:
			abort(400, message="Unexpected error {ex}".format(ex=ex))
