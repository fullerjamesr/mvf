#!/usr/bin/env python

import cryoemtools.relionstarparser as rsp
import cryoemtools.image as mrcimage
import argparse
import os.path
from collections import OrderedDict
from subprocess import run as sysrun
from subprocess import DEVNULL
import queue
import threading
import mrcfile
from PIL import Image


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


def worker(q):
    while True:
        try:
            func, fn, kwargs = q.get(block=False)
            func(fn, **kwargs)
            q.task_done()
        except queue.Empty:
            break


def mrc2png(input_file, output_dir=None, resize=None, sigma_contrast=False):
    if output_dir:
        filename = os.path.split(input_file)[-1]
        output = os.path.join(output_dir, filename) + ".png"
    else:
        output = input_file + ".png"

    with mrcfile.open(input_file) as mrc:
        data = mrc.data
    if sigma_contrast:
        mrcimage.sigma_contrast(data, sigma=sigma_contrast, new_range=(0, 255), inplace=True)
    img = mrcimage.arr_to_img(data, scale=(not sigma_contrast))
    if resize:
        # numpy data has shape (height, width). could also use img.size, which is (width, height)
        new_height = data.shape[0] * resize / data.shape[1]
        img = img.resize((resize, new_height), resample=Image.BICUBIC)
    img.save(output, format='png', compress_level=9)


def ctf2png(input_file, output_dir=None, size=None):
    if output_dir:
        filename = os.path.split(input_file)[-1]
        output = os.path.join(output_dir, filename) + ".png"
    else:
        output = input_file + ".png"
    if size:
        sysrun(['ctffind_plot_results_png.sh', input_file, output, str(size)], stdout=DEVNULL)
    else:
        sysrun(['ctffind_plot_results_png.sh', input_file, output], stdout=DEVNULL)


###
# Relion will call this script like:
# $0 --o External/jobXXX/ --in_YYY ZZZ --LABELN VALUEN --j J
parser = argparse.ArgumentParser(description="Consolidate MotionCor and CTFFind job results into a single SSV",
                                 epilog="https://github.com/fullerjamesr/mvf")
parser.add_argument("--o", required=True)
parser.add_argument("--in_mics", required=True)
parser.add_argument("--j", type=int, default=1)
parser.add_argument("--mic_png_size", type=int, default=1448)
parser.add_argument("--fft_png_size", type=int, default=None)
parser.add_argument("--ctf_png_size", type=int, default=None)
parser.add_argument("--mic_sigma_contrast", type=float, default=2.0)
args = parser.parse_args()

###
# Important files:
# * The latest CTFFind run provided as input (args.in_mics)
CTF_STAR = rsp.read_starfile(args.in_mics, tablefmt=rsp.TABLES_AS_ROW_DICTS, convertnumeric=False)
# * The MotionCor job that we're feeding off of, which sadly must be deduced from the rlnMicrographName column
moco_star_path = os.path.join(*splitall(CTF_STAR['micrographs'][0]['rlnMicrographName'])[:2],
                              'corrected_micrographs.star')
MOCO_STAR = rsp.read_starfile(moco_star_path, parseonly=['micrographs'], flatten=True, tablefmt=rsp.TABLES_AS_ROW_DICTS,
                              convertnumeric=False)
# * Pre-exiting results already in this job directory (args.o/micrographs.star)
output_path = os.path.join(args.o, 'micrographs.star')
if os.path.isfile(output_path):
    previous_output_star = rsp.read_starfile(output_path, parseonly=['micrographs'], flatten=True,
                                             tablefmt=rsp.TABLES_AS_ROW_DICTS, convertnumeric=False)
else:
    previous_output_star = []

###
# Take advantage of the time-sorted nature of the entries to skip to the new ones
#  * Add new rows to the previous output
#  * Create .png previews in the Previews/ directory for the web server of:
#   - The micrograph
#   - The FFT/idealized CTF previous written by CTFFind
#   - The gnuplot output from CTFFind
if not os.path.isdir('Previews'):
    os.mkdir('Previews')
first_new_line = len(previous_output_star)
to_do = queue.Queue()
for new_row, moco_row in zip(CTF_STAR['micrographs'][first_new_line:], MOCO_STAR[first_new_line:]):
    new_row.update(moco_row)
    previous_output_star.append(new_row)
    micrograph_path = new_row['rlnMicrographName']
    # mrc2png(micrograph_path, output_dir='Previews/', resize=args.mic_png_size, greyify=True)
    to_do.put((mrc2png, micrograph_path,
               {'output_dir': 'Previews/', 'resize': args.mic_png_size, 'sigma_contrast': args.mic_sigma_contrast}))
    ctf_image_path = new_row['rlnCtfImage'][:-4]
    # mrc2png(ctf_image_path, output_dir='Previews/', fix_scaling=True, resize=args.fft_png_size, greyify=True)
    to_do.put((mrc2png, ctf_image_path,
               {'output_dir': 'Previews/', 'resize': args.fft_png_size}))
    ctf_avrot_path = ctf_image_path[:-4] + '_avrot.txt'
    # ctf2png(ctf_avrot_path, output_dir='Previews/', size=args.ctf_png_size)
    to_do.put((ctf2png, ctf_avrot_path, {'output_dir': 'Previews/', 'size': args.ctf_png_size}))

for _ in range(args.j):
    t = threading.Thread(target=worker, args=[to_do])
    t.start()
to_do.join()


###
# Write a new micrographs.star, preserving the data_optics table too
with open(output_path, 'w') as fh:
    rsp.write_table(fh, CTF_STAR['optics'], 'optics', inputfmt=rsp.TABLES_AS_ROW_DICTS)
    rsp.write_table(fh, previous_output_star, 'micrographs', inputfmt=rsp.TABLES_AS_ROW_DICTS)

###
# Write out a .star file that will make the micrographs.star output usable in the Relion GUI as input to future jobs
with open(os.path.join(args.o, 'RELION_OUTPUT_NODES.star'), 'w') as fh:
    contents = OrderedDict((('rlnPipeLineNodeName', [output_path]), ('rlnPipeLineNodeType', [1])))
    rsp.write_table(fh, contents, block_name='output_nodes')

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
