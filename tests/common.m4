###############################################################################
# Configuration and values common to all tests.
#
# All variables declared have the prefix "M4".
###############################################################################

# The executable invoked for printing paths relative the
# list file.
m4_define(`M4_EXECUTABLE_REL_LIST',
`filelist --relative-file-argument-location')

# The executable invoked for prefixing each path with tags
m4_define(`M4_EXECUTABLE_PREPEND_TAGS',`filelist --prepend-tags')

# Installs the directory data and a given file that must
# exist under input/.
# The file is installed into the installed data directory.
m4_define(`M4_SETUP_INSTALL_DATA_AND_INPUT',
`
copy data
copy input/$1 data
')

# Utilities
# Syntax: OUTPUT-FILENAME
m4_define(`M4_SORT_STDOUT_TO_TMP_FILE',
`file -rel-tmp $1 = -stdout-from % sort @[EXACTLY_RESULT]@/stdout')
