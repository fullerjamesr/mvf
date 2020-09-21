#!/bin/bash
#
#
# Plot the results from ctffind using gnuplot
#
# Alexis Rohou, June 2014
#
# Copyright 2014 Howard Hughes Medical Institute. All rights reserved.
# Use is subject to Janelia Farm Research Campus Software Copyright 1.1
# license terms ( http://license.janelia.org/license/jfrc_copyright_1_1.html )
#
# Last modification: Tapu Shaik, April 2018
# Alexis Rohou, Dec 2018 (adding score to plot)
# James Fuller, Dec 2019: output PNGs directly for MVF, allow specification of output filename



# Parse arguments
if [[ $# -lt 1 ]] || [[ $# -gt 3 ]]; then
	echo "Usage: $(basename "$0") /path/to/output_from_ctffind_avrot.txt [/path/to/output.png] [width in pixels]"
	exit 65
fi

# input_fn = /path/to/[mic name]_avrot.txt
#  this is the output from ctffind with the curves
input_fn=$1
# input_summary_fn = /path/to/[mic_name].txt
#  this is the output from ctffind with the fitted parameters
input_summary_fn="${1%%_avrot.???}.${1##*.}"
# output_fn = [mic name].png
#  the .png output file
if [[ $# -lt 2 ]]; then
  output_fn=${1%%.???}.png
else
  output_fn=$2
fi
# Plot dimensions
plot_width=1448
if [[ $# -eq 3 ]]; then
  plot_width=$3
fi
(( plot_height=plot_width/3 ))


# Check whether gnuplot is available
if ! hash gnuplot 2>/dev/null; then
	echo "Gnuplot was not found on your system. Please make sure it is installed."
	exit 255
fi

# Check whether gnuplot >= 4.6 is available
gnuplot_version=$(  gnuplot --version | awk '{print $2}'  )
compare_result=$( echo "$gnuplot_version >= 4.6" | bc )
if [ $compare_result -le 0 ]; then
	echo "This script requires gnuplot version >= 4.6, but you have version $gnuplot_version"
	exit 255
fi

# Define a neat function
function transpose_ignore_comments {
gawk '
{
	if ($1 ~ /^#/) {
		print $0
	} else {
		for (i=1; i<=NF; i++)  {
       		a[NR,i] = $i
    	}
	}
}
NF>p { p = NF }
END {
    for(j=1; j<=p; j++) {
        str=a[1,j]
        for(i=2; i<=NR; i++){
            str=str" "a[i,j];
        }
        print str
    }
}' "$1"
}

# CTFFind outputs data in lines, but gnuplot wants things in columns
tmpfile==$(mktemp -t mvf_ctffind_plot.XXXXXXXXXX)
trap "rm -f $tmpfile;" EXIT
transpose_ignore_comments "$input_fn" > $tmpfile

# Let's grab useful values
pixel_size=$(gawk 'match($0,/Pixel size: ([0-9.]*)/,a) {print a[1]}' $input_fn)
number_of_micrographs=$(gawk 'match($0,/Number of micrographs: ([0-9]*)/,a) {print a[1]}' $input_fn)
mic_name=$(grep "Input file:" $input_fn | awk 'BEGIN {FS="Input file: "} {print $2}' | cut -d " " -f1  | sed 's/_/\\\_/g')
lines_per_micrograph=6

if [ -f $input_summary_fn ]; then
  # Let's grab values from the summary file
  i=0
  while read -a myArray
  do
    if [[ ${myArray[0]} != \#* ]]; then
      df_one[++i]=${myArray[1]}
      df_two[i]=${myArray[2]}
      angast[i]=${myArray[3]}
      pshift[i]=${myArray[4]}
      score[i]=${myArray[5]}
      maxres[i]=${myArray[6]}
	  fi
  done < $input_summary_fn
else
  df_one[0]="0"
  df_two[0]="0"
  angast[0]="0"
  pshift[0]="0"
  score[0]="0"
  maxres[0]="0"
fi

# Run Gnuplot
gnuplot > /dev/null 2>&1  <<EOF
#cat <<EOF > temp.txt
set border linewidth 1.5
set terminal pngcairo nocrop size $plot_width,$plot_height enhanced font 'Arial,14'
set output '$output_fn'

# color definitions
set style line 1 lc rgb '#0060ad' lt 1 lw 2 pt 7 # --- blue
set style line 2 lc rgb 'red'     lt 1 lw 1 pt 7 fill transparent solid 0.5 # --- red
set style line 3 lc rgb 'orange'  lt 3 lw 1 pt 7 # --- orange
set style line 4 lc rgb 'light-blue' lt 1 lw 2 pt 7 # --- light blue
set style line 5 lc rgb 'green'   lt 1 lw 2 pt 7
set style line 6 lc rgb 'gray'    lt 1 lw 2 pt 7

set xlabel 'Spatial frequency(1/Å)'
set ylabel 'Amplitude (or cross-correlation)'
set autoscale xfixmax
set yrange [-0.1:1.1]
set key outside

defocus_1_values="${df_one[*]}"
defocus_2_values="${df_two[*]}"
angast_values="${angast[*]}"
pshift_values="${pshift[*]}"
score_values="${score[*]}"
maxres_values="${maxres[*]}"

do for [current_micrograph=1:$number_of_micrographs] {
	def_1=sprintf('%.0f Å',word(defocus_1_values,current_micrograph)+0)
	def_2=sprintf('%.0f Å',word(defocus_2_values,current_micrograph)+0)
	angast=sprintf('%.1f °',word(angast_values,current_micrograph)+0)
	pshift=sprintf('%.2f rad',word(pshift_values,current_micrograph)+0)
	score=sprintf('%.3f',word(score_values,current_micrograph)+0)
	maxres=sprintf('%.2f Å',word(maxres_values,current_micrograph)+0)
	set title '$mic_name'."\nDefocus 1: ".def_1.' | Defocus 2: '.def_2.' | Azimuth: '.angast.' | Phase shift: '.pshift.' | Score: '.score.' | MaxRes: '.maxres
	plot '$tmpfile' using (\$1):(column(4+(current_micrograph-1)*$lines_per_micrograph)) w lines ls 3 title 'CTF fit', \
		 ''             using (\$1):(column(5+(current_micrograph-1)*$lines_per_micrograph)) w lines ls 1 title 'Quality of fit', \
	 	 ''             using (\$1):(column(3+(current_micrograph-1)*$lines_per_micrograph))  w lines ls 5 title 'Amplitude spectrum'
}
EOF
