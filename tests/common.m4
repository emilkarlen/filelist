###############################################################################
# This file should be included at the top of every test case file
#
# Configuration and values common to all tests.
#
# All variables declared have the prefix "M4".
###############################################################################

act-home = ../../../../src

# Aboslute name of the test directory.
m4_define(`M4_TEST_DIR',`/home/karlen/vcs/filelist/default/tests')

# Aboslute name of the src directory.
m4_define(`M4_SRC_DIR',`/home/karlen/vcs/filelist/default/src')

# The executable invoked for printing paths relative the
# list file.
m4_define(`M4_EXECUTABLE_REL_LIST',
`filelist --relative-file-argument-location')

# The executable invoked for prefixing each path with tags
m4_define(`M4_EXECUTABLE_PREPEND_TAGS',`filelist --prepend-tags')

m4_define(`M4_COMMON_TESTDATA_DIR',`M4_TEST_DIR/testdata')
m4_define(`M4_COMMON_SCRIPTS_DIR',`M4_TEST_DIR/scripts')

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

# Exit codes
m4_define(`M4_EXIT_USAGE',2)
m4_define(`M4_EXIT_INVALID_ARGUMENTS',3)
m4_define(`M4_EXIT_SYNTAX',4)
m4_define(`M4_EXIT_PRE_PROCESSING',5)
m4_define(`M4_EXIT_FILE_DOES_NOT_EXIST',m4_eval(8 + 0))
m4_define(`M4_EXIT_SHELL_COMMAND_EXECUTION_ERROR',m4_eval(8 + 1))
m4_define(`M4_EXIT_TAGS_ERROR',m4_eval(8 + 2))
