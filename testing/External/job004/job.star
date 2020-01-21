
# version 30001

data_job

_rlnJobType                            99
_rlnJobIsContinue                       1
 

# version 30001

data_joboptions_values

loop_ 
_rlnJobOptionVariable #1 
_rlnJobOptionValue #2 
  do_queue         No 
    fn_exe mvf_progress_watcher.py 
  in_3dref         "" 
 in_coords         "" 
   in_mask         "" 
    in_mic CtfFind/job003/micrographs_ctf.star 
    in_mov         "" 
   in_part         "" 
min_dedicated          1 
nr_threads         20 
other_args         "" 
param10_label         "" 
param10_value         "" 
param1_label mic_png_size 
param1_value       1024 
param2_label fft_png_size 
param2_value        512 
param3_label         "" 
param3_value         "" 
param4_label         "" 
param4_value         "" 
param5_label         "" 
param5_value         "" 
param6_label         "" 
param6_value         "" 
param7_label         "" 
param7_value         "" 
param8_label         "" 
param8_value         "" 
param9_label         "" 
param9_value         "" 
      qsub       qsub 
qsubscript /public/EM/RELION/relion/bin/relion_qsub.csh 
 queuename    openmpi 
 
