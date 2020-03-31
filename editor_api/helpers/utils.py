import re
from datetime import datetime
import json
import urllib.parse
import os.path
from decimal import Decimal

DEFAULT_STR_PAD = 16
DEFAULT_KEY_PAD = 16
DEFAULT_CODE_PAD = 12
DEFAULT_NUM_PAD = 12
DEFAULT_INT_PAD = 8
DEFAULT_DECIMALS = 5
DEFAULT_DIRECTION = "right"
DEFAULT_SPACES_AFTER = 2
NULL_STR = "null"
NULL_NUM = "0"
NON_ZERO_MIN = 0.00001


def get_valid_filename(s):
	s = s.strip().replace(' ', '_')
	return re.sub(r'(?u)[^-\w.]', '', s)


def remove_space(s, c='_'):
	if s is None or s == '':
		return s
	return s.strip().replace(' ', c)


def string_pad(val, default_pad=DEFAULT_STR_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR, spaces_after=DEFAULT_SPACES_AFTER):
	val_text = text_if_null if val is None or val == '' else remove_space(val)

	space = ""
	for x in range(0, spaces_after):
		space += " "

	if direction == "right":
		return str(val_text).rjust(default_pad) + space
	else:
		return str(val_text).ljust(default_pad) + space


def code_pad(val, default_pad=DEFAULT_CODE_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR):
	return string_pad(val, default_pad, direction, text_if_null)


def key_name_pad(prop, default_pad=DEFAULT_KEY_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR):
	val = None if prop is None else prop.name
	return string_pad(val, default_pad, direction, text_if_null)


def num_pad(val, decimals=DEFAULT_DECIMALS, default_pad=DEFAULT_NUM_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_NUM, use_non_zero_min=False):
	val_text = val
	if is_number(val):
		if use_non_zero_min and val < NON_ZERO_MIN:
			val = NON_ZERO_MIN
		val_text = "{:.{prec}f}".format(float(val), prec=decimals)

	return string_pad(val_text, default_pad, direction, text_if_null)


def exp_pad(val, decimals=4, default_pad=DEFAULT_NUM_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_NUM, use_non_zero_min=False):
	val_text = val
	if is_number(val):
		if use_non_zero_min and val == 0:
			val = 0.00000001
		val_text = "{:.{prec}E}".format(Decimal(val), prec=decimals)

	return string_pad(val_text, default_pad, direction, text_if_null)


def int_pad(val, default_pad=DEFAULT_INT_PAD, direction=DEFAULT_DIRECTION):
	return num_pad(val, 0, default_pad, direction, NULL_NUM)


def write_string(file, val, default_pad=DEFAULT_STR_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR, spaces_after=DEFAULT_SPACES_AFTER):
	file.write(string_pad(val, default_pad, direction, text_if_null, spaces_after))


def write_code(file, val, default_pad=DEFAULT_CODE_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR):
	file.write(code_pad(val, default_pad, direction, text_if_null))


def write_key_name(file, prop, default_pad=DEFAULT_KEY_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR):
	file.write(key_name_pad(prop, default_pad, direction, text_if_null))


def write_num(file, val, decimals=DEFAULT_DECIMALS, default_pad=DEFAULT_NUM_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_NUM, use_non_zero_min=False):
	file.write(num_pad(val, decimals, default_pad, direction, text_if_null, use_non_zero_min))


def write_int(file, val, default_pad=DEFAULT_INT_PAD, direction=DEFAULT_DIRECTION):
	file.write(int_pad(val, default_pad, direction))


def write_bool_yn(file, val, default_pad=DEFAULT_CODE_PAD, direction=DEFAULT_DIRECTION, text_if_null=NULL_STR):
	yn = "y" if val else "n"
	file.write(code_pad(yn, default_pad, direction, text_if_null))


def write_desc_string(file, val):
	if val is not None:
		file.write(val)


def is_number(s):
	try:
		float(s)
		return True
	except ValueError:
		return False
	except TypeError:
		return False


def json_encode_datetime(o):
	if isinstance(o, datetime):
		return o.isoformat()

	return o


def sanitize(q):
	return urllib.parse.unquote(q)


def rel_path(compare_path, curr_path):
	if curr_path is None:
		return None
	if curr_path[0].lower() != compare_path[0].lower():
		return curr_path
	
	base_path = os.path.dirname(compare_path)
	return os.path.relpath(curr_path, base_path)


def full_path(compare_path, curr_path):
	if curr_path is None:
		return None
	
	p = curr_path
	if not os.path.isabs(curr_path):
		p = os.path.normpath(os.path.join(os.path.dirname(compare_path), curr_path))
	
	return p


def are_paths_equal(p1, p2):
	p1n = os.path.normcase(os.path.realpath(p1))
	p2n = os.path.normcase(os.path.realpath(p2))
	return p1n == p2n
