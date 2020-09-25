
# version 30001

data_job

_rlnJobType                             2
_rlnJobIsContinue                       0
 

# version 30001

data_joboptions_values

loop_ 
_rlnJobOptionVariable #1 
_rlnJobOptionValue #2 
       box       1024 
   ctf_win         -1 
      dast        500 
     dfmax      50000 
     dfmin       2000 
    dfstep        100 
    do_EPA         No 
do_ignore_ctffind_params        Yes 
do_phaseshift         No 
  do_queue         No 
fn_ctffind_exe    ctffind 
fn_gctf_exe /public/EM/Gctf/bin/Gctf 
   gpu_ids         "" 
input_star_mics Schedules/mvf_basic/StreamMotion/corrected_micrographs.star 
min_dedicated          1 
    nr_mpi         40 
other_args         "" 
other_gctf_args         "" 
 phase_max        180 
 phase_min          0 
phase_step         10 
      qsub       qsub 
qsubscript /programs/i386-mac/relion/3.1-beta/bin/qsub.csh 
 queuename    openmpi 
    resmax          5 
    resmin         30 
slow_search         No 
use_ctffind4        Yes 
  use_gctf         No 
use_given_ps        Yes 
  use_noDW         No 
 
