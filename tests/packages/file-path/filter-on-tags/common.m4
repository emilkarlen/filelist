m4_include(../../../common.m4)

m4_define(`M4_STANDARD_SET',`a,b')

m4_define(`M4_RUN_WITH_OPTIONS',`filelist @[REL_FILE_ARG_OPT]@ $1 --filter-tags M4_STANDARD_SET data/tagged-files.list'
)

m4_define(`M4_RUN_WITH_OPERATOR',
`M4_RUN_WITH_OPTIONS(`--operator-for-filter-tags $1')'
)

m4_define(`M4_RUN_WITH_NEGATED_OPERATOR',
`M4_RUN_WITH_OPTIONS(`--negate-operator-for-filter-tags --operator-for-filter-tags $1')'
)

m4_define(`M4_RUN_WITH_OPERATOR_EQUALS',
`M4_RUN_WITH_OPTIONS(`$1 --operator-for-filter-tags equals')'
)
