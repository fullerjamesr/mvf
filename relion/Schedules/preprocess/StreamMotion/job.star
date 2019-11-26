
# version 30001

data_job

_rlnJobType                             1
_rlnJobIsContinue                       0
 

# version 30001

data_joboptions_values

loop_ 
_rlnJobOptionVariable #1 
_rlnJobOptionValue #2 
   bfactor $$mocoBfactor 
bin_factor $$mocoBinFactor 
do_dose_weighting        Yes 
do_own_motioncor $$mocoUseRelion 
  do_queue         No 
dose_per_frame $$movieDose 
first_frame_sum          1 
 fn_defect         "" 
fn_gain_ref $$movieGainFile 
fn_motioncor2_exe MotionCor2_1.3.0-Cuda101 
 gain_flip "No flipping (0)" 
  gain_rot "No rotation (0)" 
   gpu_ids         "" 
group_for_ps          4 
group_frames $$mocoGroupFrames 
input_star_mics Schedules/preprocess/GetMovies/movies.star 
last_frame_sum         -1 
min_dedicated          1 
    nr_mpi $$mocoMPIs 
nr_threads $$mocoThreads 
other_args         "" 
other_motioncor2_args         "" 
   patch_x $$mocoPatchX 
   patch_y $$mocoPatchY 
pre_exposure          0 
      qsub       qsub 
qsubscript /public/EM/RELION/relion/bin/relion_qsub.csh 
 queuename    openmpi 
 save_noDW        Yes 
   save_ps         No 
 
