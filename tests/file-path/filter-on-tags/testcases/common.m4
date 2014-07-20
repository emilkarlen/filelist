m4_include(../../../common.m4)

m4_define(
`M4_RUN_WITH_AB_SET_AND_OPERATOR',
`test.run.cmdline:M4_EXECUTABLE_REL_LIST --filter-tags-operator $1 --filter-tags a,b data/tagged-files.list'
)
