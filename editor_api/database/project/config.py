from peewee import *
from . import base


class File_cio_classification(base.BaseModel):
	name = CharField()


class File_cio(base.BaseModel):
	classification = ForeignKeyField(File_cio_classification, on_delete='CASCADE', related_name='files')
	order_in_class = IntegerField()
	file_name = CharField()


class Project_config(base.BaseModel):
	project_name = CharField(null=True)
	project_directory = CharField(null=True)
	editor_version = CharField(null=True)
	gis_type = CharField(null=True)
	gis_version = CharField(null=True)
	project_db = CharField(null=True)
	reference_db = CharField(null=True)
	wgn_db = CharField(null=True)
	wgn_table_name = CharField(null=True)
	weather_data_dir = CharField(null=True)
	weather_data_format = CharField(null=True)
	input_files_dir = CharField(null=True)
	input_files_last_written = DateTimeField(null=True)
	swat_last_run = DateTimeField(null=True)
	delineation_done = BooleanField(default=False)
	hrus_done = BooleanField(default=False)
	soil_table = CharField(null=True)  # Delete?
	soil_layer_table = CharField(null=True)  # Delete?

	output_last_imported = DateTimeField(null=True)
	imported_gis = BooleanField(default=False)
	is_lte = BooleanField(default=False)

	@classmethod
	def update_version(cls, version):
		q = cls.update(editor_version=version)
		return q.execute()

	@classmethod
	def update_wgn(cls, database, table):
		q = cls.update(wgn_db=database, wgn_table_name=table)
		return q.execute()

	@classmethod
	def update_weather_data(cls, dir, format):
		q = cls.update(weather_data_dir=dir, weather_data_format=format)
		return q.execute()

	@classmethod
	def update_input_files_dir(cls, dir):
		q = cls.update(input_files_dir=dir)
		return q.execute()

	@classmethod
	def update_input_files_written(cls, date):
		q = cls.update(input_files_last_written=date)
		return q.execute()

	@classmethod
	def update_swat_run(cls, date):
		q = cls.update(swat_last_run=date)
		return q.execute()

	@classmethod
	def get_or_create_default(cls, editor_version=None, project_name=None, project_db=None, reference_db=None, project_directory=None, is_lte=False):
		if cls.select().count() > 0:
			q = cls.update(editor_version=editor_version, project_name=project_name, project_db=project_db, reference_db=reference_db, project_directory=project_directory, is_lte=is_lte)
			q.execute()
			return cls.get()

		return cls.create(editor_version=editor_version, project_name=project_name, project_db=project_db, reference_db=reference_db, delineation_done=False, hrus_done=False, is_lte=is_lte)
