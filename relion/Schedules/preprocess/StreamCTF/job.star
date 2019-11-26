
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
      dast $$ctffindAstig 
     dfmax $$ctffindMaxDefocus 
     dfmin $$ctffindMinDefocus 
    dfstep        100 
    do_EPA         No 
do_ignore_ctffind_params        Yes 
do_phaseshift         No 
  do_queue         No 
fn_ctffind_exe    ctffind 
fn_gctf_exe /public/EM/Gctf/bin/Gctf 
   gpu_ids         "" 
input_star_mics Schedules/preprocess/StreamMotion/corrected_micrographs.star 
min_dedicated          1 
    nr_mpi $$ctffindMPIs 
other_args         "" 
other_gctf_args         "" 
 phase_max        180 
 phase_min          0 
phase_step         10 
      qsub       qsub 
qsubscript /public/EM/RELION/relion/bin/relion_qsub.csh 
 queuename    openmpi 
    resmax $$ctffindMaxRes 
    resmin $$ctffindMinRes 
slow_search $$ctffindExhaustive 
use_ctffind4        Yes 
  use_gctf         No 
use_given_ps         No 
  use_noDW        Yes 
 
