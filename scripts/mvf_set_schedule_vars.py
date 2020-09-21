#!/usr/bin/env python

import argparse
import os.path
from sys import argv
from distutils.util import strtobool
import cryoemtools.relionstarparser as rsp

SCRIPT_NAME = os.path.basename(argv[0])

parser = argparse.ArgumentParser(description="Change common variables in a Relion schedule",
                                 epilog="https://github.com/fullerjamesr/mvf")
parser.add_argument("--no-backup", action="store_true",
                    help="Don't save original schedule.star as schedule.star.bak")
parser.add_argument("schedule",
                    help="Name of a schedule in the current Relion project directory, or the path to a schedule "
                         "folder containing a schedule.star, or absolute path to schedule.star")
args = parser.parse_args()

# args.schedule can be:
#  * Just a name, in which case ./Schedules/<schedule> should exist
#  * The path to the schedule's location, in which case <schedule>/schedule.star should exist
#  * The path to a .star file, in which case that <schedule> file should exist
file_path = None
if os.path.isfile(args.schedule):
    file_path = args.schedule
elif os.path.isdir(args.schedule) and os.path.isfile(os.path.join(args.schedule, 'schedule.star')):
    file_path = os.path.join(args.schedule, 'schedule.star')
elif os.path.isfile(os.path.join('Schedules', args.schedule, 'schedule.star')):
    file_path = os.path.join('Schedules', args.schedule, 'schedule.star')

if file_path is None:
    parser.exit(1, "{:s}: could not locate a schedule.star file given '{:s}'\n".format(SCRIPT_NAME, args.schedule))

try:
    schedule = rsp.read_star(file_path, tablefmt=rsp.TableFormat.LIST_OF_ROW_DICTS)
    print("Reading {:s}...".format(file_path))
except ValueError:
    parser.exit(1, "{:s}: error parsing {:s}".format(SCRIPT_NAME, file_path))

print("\nEmpty answers keep original/current values\n")

if 'schedule_floats' in schedule:
    for row in schedule['schedule_floats']:
        var_name = row['rlnScheduleFloatVariableName']
        var_value = row['rlnScheduleFloatVariableResetValue']
        if var_name.startswith("set_"):
            while True:
                new_value = input("float {:s} (currently: {:f}): ".format(var_name, var_value)).strip()
                if len(new_value) == 0:
                    break
                try:
                    new_value = float(new_value)
                    row['rlnScheduleFloatVariableResetValue'] = new_value
                    break
                except ValueError:
                    pass

if 'schedule_bools' in schedule:
    for row in schedule['schedule_bools']:
        var_name = row['rlnScheduleBooleanVariableName']
        var_value = bool(row['rlnScheduleBooleanVariableResetValue'])
        if var_name.startswith("set_"):
            while True:
                new_value = input("bool {:s} (currently: {}): ".format(var_name, var_value)).strip()
                if len(new_value) == 0:
                    break
                try:
                    new_value = int(bool(strtobool(new_value)))
                    row['rlnScheduleBooleanVariableResetValue'] = new_value
                    break
                except ValueError:
                    pass

if 'schedule_strings' in schedule:
    for row in schedule['schedule_strings']:
        var_name = row['rlnScheduleStringVariableName']
        var_value = row['rlnScheduleStringVariableResetValue']
        if var_name.startswith("set_"):
            while True:
                new_value = input("string {:s} (currently: {:s}): ".format(var_name, var_value)).strip()
                if len(new_value) == 0:
                    break
                elif not any(c.isspace() for c in new_value):
                    row['rlnScheduleStringVariableResetValue'] = new_value
                    break

# backup by default
if not args.no_backup:
    os.rename(file_path, file_path + ".bak")
    print("\nBacked up original schedule.star to schedule.star.bak")

with open(file_path, 'w') as fh:
    rsp.write_dict_block(fh, schedule['schedule_general'], block_name='schedule_general')
    for block in ['schedule_floats', 'schedule_bools', 'schedule_strings', 'schedule_operators', 'schedule_jobs',
                  'schedule_edges']:
        rsp.write_table(fh, schedule[block], block_name=block, inputfmt=rsp.TableFormat.LIST_OF_ROW_DICTS)

print("\nFinished. You probably want to call 'relion_scheduler --reset --schedule <schedule name>' from the Relion "
      "project directory before running the schedule.")
