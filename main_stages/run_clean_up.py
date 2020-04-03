'''
date        : 31/03/2020
description : this module cleans up unnecessary files

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import shutil
import os
import sys

base = sys.argv[1]

if os.path.isdir("{base}/__pycache__".format(base=base)):
    shutil.rmtree("{base}/__pycache__".format(base=base))

