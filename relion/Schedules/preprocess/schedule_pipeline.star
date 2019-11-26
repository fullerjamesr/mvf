
# version 30001

data_pipeline_general

_rlnPipeLineJobCounter                       8
 

# version 30001

data_pipeline_processes

loop_ 
_rlnPipeLineProcessName #1 
_rlnPipeLineProcessAlias #2 
_rlnPipeLineProcessType #3 
_rlnPipeLineProcessStatus #4 
Schedules/preprocess/GetMovies/       None            0            1 
Schedules/preprocess/StreamMotion/       None            1            1 
Schedules/preprocess/StreamCTF/       None            2            1 
 

# version 30001

data_pipeline_nodes

loop_ 
_rlnPipeLineNodeName #1 
_rlnPipeLineNodeType #2 
Schedules/preprocess/GetMovies/movies.star            0 
Schedules/preprocess/StreamMotion/corrected_micrographs.star            1 
Schedules/preprocess/StreamMotion/logfile.pdf           13 
Schedules/preprocess/AllMovies/corrected_micrographs.star            1 
Schedules/preprocess/StreamCTF/micrographs_ctf.star            1 
Schedules/preprocess/StreamCTF/logfile.pdf           13 
 

# version 30001

data_pipeline_input_edges

loop_ 
_rlnPipeLineEdgeFromNode #1 
_rlnPipeLineEdgeProcess #2 
Schedules/preprocess/GetMovies/movies.star Schedules/preprocess/StreamMotion/ 
Schedules/preprocess/StreamMotion/corrected_micrographs.star Schedules/preprocess/StreamCTF/ 
 

# version 30001

data_pipeline_output_edges

loop_ 
_rlnPipeLineEdgeProcess #1 
_rlnPipeLineEdgeToNode #2 
Schedules/preprocess/GetMovies/ Schedules/preprocess/GetMovies/movies.star 
Schedules/preprocess/StreamMotion/ Schedules/preprocess/StreamMotion/corrected_micrographs.star 
Schedules/preprocess/StreamMotion/ Schedules/preprocess/StreamMotion/logfile.pdf 
Schedules/preprocess/StreamCTF/ Schedules/preprocess/StreamCTF/micrographs_ctf.star 
Schedules/preprocess/StreamCTF/ Schedules/preprocess/StreamCTF/logfile.pdf 
 
