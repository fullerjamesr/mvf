#!/usr/bin/env python

import cryoemtools.relionstarparser as rsp
import argparse
import os.path


# Why doesn't Python have a builtin to fully explode a path? Dumb.
def splitall(path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[1] == path:
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


###
# Relion will call this script like:
# $0 --o External/jobXXX/ --in_YYY ZZZ --LABELN VALUEN --j J
parser = argparse.ArgumentParser(description="Consolidate MotionCor and CTFFind job results into a single SSV",
                                 epilog="https://github.com/fullerjamesr/mvf")
parser.add_argument("--o", required=True)
parser.add_argument("--in_mics", required=True)
parser.add_argument("--j")
args = parser.parse_args()

###
# Important files:
# * The latest CTFFind run provided as input (args.in_mics)
ctf_star = rsp.read_starfile(args.in_mics, tablefmt=rsp.TABLES_AS_ROW_DICTS, convertnumeric=False)
# * The MotionCor job that we're feeding off of, which sadly must be deduced from the rlnMicrographName column
moco_star_path = os.path.join(*splitall(ctf_star['micrographs'][0]['rlnMicrographName'])[:2], 'corrected_micrographs.star')
moco_star = rsp.read_starfile(moco_star_path, parseonly=['micrographs'], flatten=True, tablefmt=rsp.TABLES_AS_ROW_DICTS,
                              convertnumeric=False)
# * Pre-exiting results already in this job directory (args.o/micrographs.star)
output_path = os.path.join(args.o, 'micrographs.star')
if os.path.isfile(output_path):
    previous_output_star = rsp.read_starfile(output_path, parseonly=['micrographs'], flatten=True,
                                             tablefmt=rsp.TABLES_AS_ROW_DICTS, convertnumeric=False)
else:
    previous_output_star = []

###
# Take advantage of the sorted nature of each star
first_new_line = len(previous_output_star)
for new_row, moco_row in zip(ctf_star['micrographs'][first_new_line:], moco_star[first_new_line:]):
    new_row.update(moco_row)
    previous_output_star.append(new_row)


###
# Write a new micrographs.star, preserving the data_optics table too
with open(output_path, 'w') as fh:
    rsp.write_table(fh, ctf_star['optics'], 'optics', inputfmt=rsp.TABLES_AS_ROW_DICTS)
    rsp.write_table(fh, previous_output_star, 'micrographs', inputfmt=rsp.TABLES_AS_ROW_DICTS)

###
# Write out hints to the frontend as a simple file listing the output dir and micrograph count
with open('.mvf_progress_hint', 'w') as fh:
    fh.write(output_path)
    fh.write(" ")
    fh.write(str(len(previous_output_star)))
    fh.write("\n")

###
# Relion knows a job is complete when the program touches a file names RELION_JOB_EXIT_SUCCESS in the job directory
# TODO: implement RELION_JOB_EXIT_FAILURE in some way nicer than wrapping this whole thing in a giant try/except block
with open(os.path.join(args.o, 'RELION_JOB_EXIT_SUCCESS'), 'w') as fh:
    pass
