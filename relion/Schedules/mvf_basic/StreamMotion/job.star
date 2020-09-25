
# version 30001

data_job

_rlnJobType                             1
_rlnJobIsContinue                       0
 

# version 30001

data_joboptions_values

loop_ 
_rlnJobOptionVariable #1 
_rlnJobOptionValue #2 
   bfactor        500 
bin_factor          2 
do_dose_weighting        Yes 
do_own_motioncor        Yes 
  do_queue         No 
dose_per_frame $$set_frame_dose 
first_frame_sum          1 
 fn_defect         "" 
fn_gain_ref $$set_gain_file_path 
fn_motioncor2_exe /public/EM/MOTIONCOR2/MotionCor2 
 gain_flip "No flipping (0)" 
  gain_rot "No rotation (0)" 
   gpu_ids          0 
group_for_ps $$set_ctf_powerspectrum_window 
group_frames          1 
input_star_mics Schedules/mvf_basic/UpdateMovies/movies.star 
last_frame_sum         -1 
min_dedicated          1 
    nr_mpi         10 
nr_threads          8 
other_args "--do_at_most 200" 
other_motioncor2_args         "" 
   patch_x          7 
   patch_y          5 
pre_exposure          0 
      qsub       qsub 
qsubscript /programs/i386-mac/relion/3.1-beta/bin/qsub.csh 
 queuename    openmpi 
 save_noDW         No 
   save_ps        Yes 
 
