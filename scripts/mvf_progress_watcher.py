#!/usr/bin/env python

import sys
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
import atexit


def explode_path(path):
    """
    Explode a path into a list of its parts by repeated calls to `os.path.split`

    Has same corner cases as the underlying `os.path.split`. Corner cases of note:
    * `explode_path('/path/to/file') # Leading slashes included` => `['/', 'path', 'to', 'file']`
    * `explode_path('/path/to/folder/') # Trailing slashes yield an empty item` => `['/', 'path', 'to', 'folder', '']`
    Treating these cases this way ensures that `path` could be reassembled by call(s) to `os.path.join`

    Parameters
    ----------
    path : str or os.PathLike

    Returns
    -------
    list of str
    """
    allparts = []
    while True:
        parts = os.path.split(path)
        if parts[1] == path:
            allparts.insert(0, parts[1])
            break
        elif set(parts[0]) == {'/'}:
            allparts = parts + allparts
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts


def threaded_worker(q):
    """
    This function will consume and execute the contents of a threading.Queue object until it is empty.

    Expected items in the queue are tuples of (function, primary argument, **kwargs)

    Parameters
    ----------
    q : threading.Queue

    Returns
    -------
    None
    """
    while True:
        try:
            func, fn, kwargs = q.get(block=False)
            func(fn, **kwargs)
            q.task_done()
        except queue.Empty:
            break


def mrc2png(input_file, output_dir=None, resize=0, sigma_contrast=0.0):
    """
    Convert a .mrc file to a .png image. The output filename will be `input_file` with the .png extension appended.

    Parameters
    ----------
    input_file : str or os.PathLike
        The path to a .mrc file to read and convert
    output_dir : str or os.PathLike, optional
        The path to a directory in which to save the file
    resize : int, optional
        Resize the output so that it has this width (in pixels)
    sigma_contrast : float, optional
        Transform the .mrc data to this sigma contrast before PNG encoding

    Returns
    -------
    None
    """
    if output_dir:
        filename = os.path.split(input_file)[-1]
        output = os.path.join(output_dir, filename) + ".png"
    else:
        output = input_file + ".png"

    with mrcfile.open(input_file) as mrc:
        data = mrc.data
    # mrcfile sets the writeable flag to 0 on the underlying data array, but it seems to remain in memory OK?
    # it seems good to avoid making a copy
    data.setflags(write=1)
    # CTFFind writes out .mrc files with an improperly-set header byte so an extra dimension gets added by mrcfile
    if len(data.shape) > 2:
        data = data.squeeze()
    if sigma_contrast:
        mrcimage.sigma_contrast(data, sigma=sigma_contrast, new_range=(0, 255), inplace=True)
    img = mrcimage.arr_to_img(data, scale=(not sigma_contrast))
    if resize:
        # numpy data has shape (height, width). could also use img.size, which is (width, height)
        new_height = int(data.shape[0] * resize / data.shape[1])
        img = img.resize((resize, new_height), resample=Image.LANCZOS)
    img.save(output, format='png', compress_level=9)


def ctf2png(input_file, output_dir=None, size=None):
    """
    Wrapper around the ctffind_plot_results_png.sh script, used to emit the familiar CTFFind results plots to .png file

    Parameters
    ----------
    input_file : str or os.PathLike
        The path to a CTFFind output _avrot.txt file, the required argument to the ctffind_plot_results script
    output_dir : str or os.PathLike, optional
        The path to a directory in which to save the .png file
    size : int, optional
        Resize the output so that it has this width (in pixels)

    Returns
    -------
    None
    """
    if output_dir:
        filename = os.path.split(input_file)[-1]
        output = os.path.join(output_dir, filename) + ".png"
    else:
        output = input_file + ".png"
    if size:
        sysrun(['ctffind_plot_results_png.sh', input_file, output, str(size)], stdout=DEVNULL)
    else:
        sysrun(['ctffind_plot_results_png.sh', input_file, output], stdout=DEVNULL)


def touch_file(file_path):
    """
    Mimic the Unix `touch` command: Create the specified file if it doesn't exist, then update its access time

    Parameters
    ----------
    file_path : str or os.PathLike

    Returns
    -------
    None
    """
    with open(file_path, 'a'):
        try:
            os.utime(file_path, None)
        except OSError:
            pass  # File deleted between open() and os.utime() calls


def normal_exit(job_dir):
    """
    Indicate to Relion that the job has ended normally

    Parameters
    ----------
    job_dir : str or os.PathLike

    Returns
    -------
    None
    """
    touch_file(os.path.join(job_dir, 'RELION_JOB_EXIT_SUCCESS'))


def fail_exit(job_dir):
    """
    Indicate to Relion that the job has ended with an unexpected error

    Parameters
    ----------
    job_dir : str or os.PathLike

    Returns
    -------
    None
    """
    touch_file(os.path.join(job_dir, 'RELION_JOB_EXIT_FAILURE'))


def signal_failure_factory(job_dir):
    def signal_failure(*args):
        atexit.unregister(normal_exit)
        atexit.register(fail_exit, job_dir)
        sys.__excepthook__(*args)
    return signal_failure


def clear_prior_exits(job_dir):
    """
    Cleanup any indicators of previous Relion exit statuses in `job_dir`

    Parameters
    ----------
    job_dir : str or os.PathLike

    Returns
    -------
    None
    """
    for f in ('RELION_JOB_EXIT_SUCCESS', 'RELION_JOB_EXIT_FAILURE'):
        try:
            os.remove(os.path.join(job_dir, f))
        except FileNotFoundError:
            pass


def main():
    ###
    # Relion will call this script like:
    #     $0 --o External/jobXXX/ --in_YYY ZZZ --LABELN VALUEN --j J
    # and the current working directory will be the root of the Relion project at hand
    parser = argparse.ArgumentParser(description="Consolidate Relion MotionCorr and CtfFind jobs and generate preview "
                                                 "images for use with the mvf web display",
                                     epilog="https://github.com/fullerjamesr/mvf")
    parser.add_argument("--o", required=True)
    parser.add_argument("--in_mics", required=True)
    parser.add_argument("--j", type=int, default=1)
    parser.add_argument("--mic_png_size", type=int, default=1448)
    parser.add_argument("--fft_png_size", type=int, default=0)
    parser.add_argument("--ctf_png_size", type=int, default=0)
    parser.add_argument("--mic_sigma_contrast", type=float, default=2.0)
    args = parser.parse_args()

    # Engage the scaffolding that will touch the appropriate filenames to indicate success or failure to Relion
    atexit.register(normal_exit, args.o)
    sys.excepthook = signal_failure_factory(args.o)
    # ...and remove any old status indicator files
    clear_prior_exits(args.o)

    ctf_star = rsp.read_star(args.in_mics, tablefmt=rsp.TableFormat.LIST_OF_ROW_DICTS, convert_numeric=False)
    # no point in running if there's nothing to process
    if 'micrographs' not in ctf_star or len(ctf_star['micrographs'] == 0):
        return

    # TODO: Huge assumption past this point: that any input to this job is a superset of the rows already processed,
    #   that the two are sorted the same, all come from the same single MotionCorr job, and nothing needs to change with
    #   the optics groups.

    output_path = os.path.join(args.o, 'micrographs.star')
    if os.path.isfile(output_path):
        previous_output_mics = rsp.read_star(output_path, block_list=['micrographs'], flatten=True,
                                             convert_numeric=False,
                                             tablefmt=rsp.TableFormat.LIST_OF_ROW_DICTS)
    else:
        previous_output_mics = []

    # ...or if there's nothing new
    if len(previous_output_mics) == len(ctf_star['micrographs']):
        return

    # rlnMicrographName records will be like:
    #     MotionCorr/jobXXX/arbitrary/raw/data/organization/file.mrc
    # Need to extract the first two path chunks to locate the MotionCorr output directory
    moco_star_path = os.path.join(*explode_path(ctf_star['micrographs'][0]['rlnMicrographName'])[:2],
                                  'corrected_micrographs.star')
    moco_star = rsp.read_star(moco_star_path, block_list=['micrographs'], flatten=True, convert_numeric=False,
                              tablefmt=rsp.TableFormat.LIST_OF_ROW_DICTS)

    # Take advantage of the time-sorted nature of the entries to skip to the new ones, do the following:
    #  * Add new rows to the previous output
    #  * For new rows, create .png previews in the Previews/ directory for the web server of:
    #   - The micrograph
    #   - The FFT/idealized CTF previews written by CTFFind
    #   - The gnuplot output from CTFFind
    if not os.path.isdir('Previews'):
        os.mkdir('Previews')
    first_new_line = len(previous_output_mics)
    to_do = queue.Queue()
    for new_row, moco_row in zip(ctf_star['micrographs'][first_new_line:], moco_star[first_new_line:]):
        new_row.update(moco_row)
        previous_output_mics.append(new_row)

        micrograph_path = new_row['rlnMicrographName']
        ctf_fft_path = new_row['rlnCtfImage'][:-4]
        ctf_avrot_path = ctf_fft_path[:-4] + '_avrot.txt'

        # mrc2png(micrograph_path, output_dir='Previews/',
        #         resize=args.mic_png_size, sigma_contrast=args.mic_sigma_contrast)
        to_do.put((mrc2png, micrograph_path,
                   {'output_dir': 'Previews/', 'resize': args.mic_png_size, 'sigma_contrast': args.mic_sigma_contrast}))
        # mrc2png(ctf_fft_path, output_dir='Previews/', resize=args.fft_png_size)
        to_do.put((mrc2png, ctf_fft_path,
                   {'output_dir': 'Previews/', 'resize': args.fft_png_size}))
        # ctf2png(ctf_avrot_path, output_dir='Previews/', size=args.ctf_png_size)
        to_do.put((ctf2png, ctf_avrot_path, {'output_dir': 'Previews/', 'size': args.ctf_png_size}))

    for _ in range(args.j):
        t = threading.Thread(target=threaded_worker, args=[to_do])
        t.start()
    to_do.join()

    # Write a new micrographs.star, preserving the data_optics table too
    with open(output_path, 'w') as fh:
        rsp.write_table(fh, ctf_star['optics'], block_name='optics', inputfmt=rsp.TableFormat.LIST_OF_ROW_DICTS)
        rsp.write_table(fh, previous_output_mics, block_name='micrographs', inputfmt=rsp.TableFormat.LIST_OF_ROW_DICTS)

    # Write out a .star file that will make the micrographs.star output usable in the Relion GUI as input to future jobs
    with open(os.path.join(args.o, 'RELION_OUTPUT_NODES.star'), 'w') as fh:
        contents = OrderedDict((('rlnPipeLineNodeName', [output_path]), ('rlnPipeLineNodeType', [1])))
        rsp.write_table(fh, contents, block_name='output_nodes')

    # Write out hints to the mvf app frontend as a simple file listing the output dir and micrograph count
    with open('.mvf_progress_hint', 'w') as fh:
        fh.write(output_path)
        fh.write(" ")
        fh.write(str(len(previous_output_mics)))
        fh.write("\n")


if __name__ == '__main__':
    main()
