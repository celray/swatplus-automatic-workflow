import json

class Unbuffered(object):
   def __init__(self, stream):
	   self.stream = stream
   def write(self, data):
	   self.stream.write(data)
	   self.stream.flush()
   def writelines(self, datas):
	   self.stream.writelines(datas)
	   self.stream.flush()
   def __getattr__(self, attr):
	   return getattr(self.stream, attr)

class ExecutableApi:
	def emit_progress(self, percent, message):
		print('\t - percent: {0} - {1}'.format(str(percent).rjust(3), message))

