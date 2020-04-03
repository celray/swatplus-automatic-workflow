'''
date        : 03/04/2020
description : this module logs and tracks progress
              for trouble shooring purposes

author      : Celray James CHAWANDA
contact     : celray.chawanda@outlook.com
licence     : MIT 2020
'''

import sys
import datetime

# sys.path.insert(0, sys.argv[1])


class log:
    def __init__(self, log_fn):
        self.fn = log_fn
        self.start_time = datetime.datetime.now()

    def initialise(self, write_to_file=True):
        if not write_to_file:
            return

        with open(self.fn, "w") as log_file:
            log_file.write("swatplus_aw log file writen on {date}.\n\n".format(
                date="{dd}-{mm}-{yy}".format(
                    dd=datetime.datetime.now().day,
                    mm=datetime.datetime.now().month,
                    yy=datetime.datetime.now().year,
                )
            ))

    def info(self, message, write_to_file=True):
        if not write_to_file:
            return
        with open(self.fn, "a") as log_file:
            log_file.write("{time}: {msg}\n".format(
                time="{hh}:{mm}:{ss}".format(
                    hh=datetime.datetime.now().hour,
                    mm=datetime.datetime.now().minute,
                    ss=datetime.datetime.now().second),
                msg=message
            ))

    def error(self, message, write_to_file=True):
        if not write_to_file:
            return
        with open(self.fn, "a") as log_file:
            log_file.write("\n{time}: error! : {msg}\n".format(
                time="{hh}:{mm}:{ss}".format(
                    hh=datetime.datetime.now().hour,
                    mm=datetime.datetime.now().minute,
                    ss=datetime.datetime.now().second),
                msg=message
            ))

    def warn(self, message, write_to_file=True):
        if not write_to_file:
            return
        with open(self.fn, "a") as log_file:
            log_file.write("\n{time}: warning : {msg}\n".format(
                time="{hh}:{mm}:{ss}".format(
                    hh=datetime.datetime.now().hour,
                    mm=datetime.datetime.now().minute,
                    ss=datetime.datetime.now().second),
                msg=message
            ))

