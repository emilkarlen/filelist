m4_include(../../../../common.m4)

m4_define(`M4_STANDARD_SET',`a,b')

m4_define(
`M4_RUN_WITH_OPERATOR',
`test.run.cmdline:M4_EXECUTABLE_REL_LIST --operator-for-filter-tags $1 --filter-tags M4_STANDARD_SET data/tagged-files.list'
)

m4_define(
`M4_RUN_WITH_NEGATED_OPERATOR',
`test.run.cmdline:M4_EXECUTABLE_REL_LIST --negate-operator-for-filter-tags --operator-for-filter-tags $1 --filter-tags M4_STANDARD_SET data/tagged-files.list'
)
