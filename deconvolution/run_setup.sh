#!/bin/bash

#!/bin/bash


  # "name" of the job (optional)
#PBS -N my_serial_job         


  # requested running time (required!)
#PBS -l walltime=01:20:00

  # specification (required!)
  #   nodes=   number of nodes; 1 for serial; 1 or more for parallel
  #   ppn=     number of processors per node; 1 for serial; up to 8
  #   if you want your "private" node: ppn=8
  #   mem=     memory required
#PBS -l nodes=1:ppn=1

#PBS -l mem=80gb


module load Julia/1.11.6-linux-x86_64
module load Anaconda3/2024.06-1


julia setup.jl
