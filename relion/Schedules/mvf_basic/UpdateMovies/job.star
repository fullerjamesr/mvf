
# version 30001

data_job

_rlnJobType                             0
_rlnJobIsContinue                       0
 

# version 30001

data_joboptions_values

loop_ 
_rlnJobOptionVariable #1 
_rlnJobOptionValue #2 
        Cs        2.7 
        Q0 $$set_ctf_amp_contrast 
    angpix $$set_angpix 
beamtilt_x          0 
beamtilt_y          0 
  do_other         No 
  do_queue         No 
    do_raw        Yes 
fn_in_other    ref.mrc 
 fn_in_raw $$set_movie_import_glob 
    fn_mtf $$set_mtf_file_path 
is_multiframe        Yes 
        kV $$set_voltage 
min_dedicated          1 
 node_type "Particle coordinates (*.box, *_pick.star)" 
optics_group_name opticsGroup1 
optics_group_particles         "" 
other_args         "" 
      qsub       qsub 
qsubscript /programs/i386-mac/relion/3.1-beta/bin/qsub.csh 
 queuename    openmpi 
 
