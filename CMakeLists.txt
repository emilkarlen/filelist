###############################################################################
# Copyright 2014 Emil Karlén.
# 
# This file is part of file-name-resolver.
# 
# Wilde is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Wilde is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Wilde.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

cmake_minimum_required(VERSION 2.8)

project(file-name-lister NONE)

set (CMAKE_INSTALL_PREFIX /home/karlen/tmp/test-install/${CMAKE_PROJECT_NAME})

install(PROGRAMS src/file-name-lister DESTINATION bin)


###############################################################################
# - test -
###############################################################################


enable_testing()

find_program(SIMPTESTCASE simptestcase)

configure_file(
  ${CMAKE_SOURCE_DIR}/tests/common.m4.in
  ${CMAKE_SOURCE_DIR}/tests/common.m4
) 

###############################################################################
# Macro for test using simptestcase, with a test case that uses M4.
#
# Argument is the name of the test case file:
# - without the test directory name prefix ("tests/")
# - without the file type suffix (".m4.simptestcase")
#
# The argument will be used as-is as the tests name.
###############################################################################
macro (simptestcase testFileNameHead)
  add_test (
    NAME ${testFileNameHead}
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMAND ${SIMPTESTCASE} --m4 -v tests/${testFileNameHead}.m4.simptestcase
    )
endmacro (simptestcase)


###############################################################################
# Testcases
###############################################################################


simptestcase (invalid-usage-no-arguments)
simptestcase (invalid-arguments-file-does-not-exist)

simptestcase (parse/invalid-instruction-name)
simptestcase (parse/invalid-line-syntax)

simptestcase (comments-blanklines-single-file)

simptestcase (file-existing)
simptestcase (file-existing-relative-file-argument)
simptestcase (file-non-existing)

simptestcase (list-existing-directory)
simptestcase (list-existing-directory-relative-file-argument)

simptestcase (include-existing--relative-file-argument)
simptestcase (include-existing-in-same-dir)
simptestcase (include-existing-in-subdir)
simptestcase (include-non-existing)
simptestcase (include-existing-dir)
