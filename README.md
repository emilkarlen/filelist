# filelist


Command line program for administrating distributed lists of files


# Description


Prints a list of file-paths given list-files containing file-path
specifications.

This is a tool for maintaining a distributed list of files that can be
accessed via one ore more top level list-files.

The printed paths are all relative the same location - the current
working directory, so that they can be easily accessed.

A file-path specification is just a file-name that is relative the
location of the list-file.
The file-path specifications can be distributed across several list-
files, via an inclusion instruction. The file-paths in each included
list-file is relative the location of the included list-file.

File-path can be "tagged" via a special instruction (see below). Via
options the program can be set to output only files who's tags match a
given condition.


# Project status


Source organisation and distribution is not yet done.
