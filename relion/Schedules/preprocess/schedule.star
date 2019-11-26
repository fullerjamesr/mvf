
# version 30001

data_schedule_general

_rlnScheduleName                       Schedules/preprocess/
_rlnScheduleCurrentNodeName            GetMovies
 

# version 30001

data_schedule_floats

loop_ 
_rlnScheduleFloatVariableName #1 
_rlnScheduleFloatVariableValue #2 
_rlnScheduleFloatVariableResetValue #3 
ampContrast     0.100000     0.100000 
    angpix     0.530000     0.530000 
ctffindAstig   500.000000   500.000000 
ctffindMPIs    20.000000    20.000000 
ctffindMaxDefocus 50000.000000 50000.000000 
ctffindMaxRes     5.000000     5.000000 
ctffindMinDefocus  4000.000000  4000.000000 
ctffindMinRes    30.000000    30.000000 
mocoBfactor   500.000000   500.000000 
mocoBinFactor     2.000000     2.000000 
mocoGroupFrames     1.000000     1.000000 
  mocoMPIs     1.000000     1.000000 
mocoPatchX     7.000000     7.000000 
mocoPatchY     5.000000     5.000000 
mocoThreads    20.000000    20.000000 
movieAngPix     0.530000     0.530000 
movieCheckDelay    20.000000    20.000000 
movieCountDelta     5.000000     5.000000 
 movieDose     1.310000     1.310000 
mut_movieCount    50.000000     0.000000 
mut_movieCountShadow    55.000000     0.000000 
   voltage   300.000000   300.000000 
 

# version 30001

data_schedule_bools

loop_ 
_rlnScheduleBooleanVariableName #1 
_rlnScheduleBooleanVariableValue #2 
_rlnScheduleBooleanVariableResetValue #3 
ctffindExhaustive            0            0 
mocoUseRelion            0            0 
mut_movieCountProceed            0            0 
 

# version 30001

data_schedule_strings

loop_ 
_rlnScheduleStringVariableName #1 
_rlnScheduleStringVariableValue #2 
_rlnScheduleStringVariableResetValue #3 
movieDir Micrographs/*.tif Micrographs/*.tif 
movieGainFile Micrographs/gainref.mrc Micrographs/gainref.mrc 
mtfFile         ""         "" 
ro_moviesStar Schedules/preprocess/GetMovies/movies.star Schedules/preprocess/GetMovies/movies.star 
ro_str_movies     movies     movies 
 

# version 30001

data_schedule_operators

loop_ 
_rlnScheduleOperatorName #1 
_rlnScheduleOperatorType #2 
_rlnScheduleOperatorOutput #3 
_rlnScheduleOperatorInput1 #4 
_rlnScheduleOperatorInput2 #5 
WAIT_movieCheckDelay       wait  undefined movieCheckDelay  undefined 
mut_movieCount=COUNT_IMGS_ro_moviesStar_ro_str_movies float=count_images mut_movieCount ro_moviesStar ro_str_movies 
mut_movieCountProceed=mut_movieCount_GE_mut_movieCountShadow    bool=ge mut_movieCountProceed mut_movieCount mut_movieCountShadow 
mut_movieCountShadow=mut_movieCount_PLUS_movieCountDelta float=plus mut_movieCountShadow mut_movieCount movieCountDelta 
 

# version 30001

data_schedule_jobs

loop_ 
_rlnScheduleJobNameOriginal #1 
_rlnScheduleJobName #2 
_rlnScheduleJobMode #3 
_rlnScheduleJobHasStarted #4 
 GetMovies Import/job008/   continue            1 
 StreamCTF CtfFind/job010/   continue            1 
StreamMotion MotionCorr/job009/   continue            1 
 

# version 30001

data_schedule_edges

loop_ 
_rlnScheduleEdgeInputNodeName #1 
_rlnScheduleEdgeOutputNodeName #2 
_rlnScheduleEdgeIsFork #3 
_rlnScheduleEdgeOutputNodeNameIfTrue #4 
_rlnScheduleEdgeBooleanVariable #5 
mut_movieCountShadow=mut_movieCount_PLUS_movieCountDelta WAIT_movieCheckDelay            0  undefined  undefined 
WAIT_movieCheckDelay  GetMovies            0  undefined  undefined 
 GetMovies mut_movieCount=COUNT_IMGS_ro_moviesStar_ro_str_movies            0  undefined  undefined 
mut_movieCount=COUNT_IMGS_ro_moviesStar_ro_str_movies mut_movieCountProceed=mut_movieCount_GE_mut_movieCountShadow            0  undefined  undefined 
mut_movieCountProceed=mut_movieCount_GE_mut_movieCountShadow WAIT_movieCheckDelay            1 StreamMotion mut_movieCountProceed 
StreamMotion  StreamCTF            0  undefined  undefined 
 StreamCTF mut_movieCountShadow=mut_movieCount_PLUS_movieCountDelta            0  undefined  undefined 
 
