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

project(file-name-lister/test NONE)


find_program(SIMPTESTCASE simptestcase)

configure_file(
  common.m4.in
  ${CMAKE_CURRENT_SOURCE_DIR}/common.m4
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
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND ${SIMPTESTCASE} --m4 -v ${testFileNameHead}.m4.simptestcase
    )
endmacro (simptestcase)

###############################################################################
# Macro for test using simptestcase, with a test case that uses M4.
#
# Arguments:
# - testPkgDir relative path of the "home" of the test package.
#              Inside this dir, testcases must be located in
#              in the "testcases" directory.
#              This values is also used as part of the test's name.
# - testFileNameHead
#              Name of the "head" of the file - the part before the suffix
#              ".m4.simptestcase".
#              This value is also used as part of the test's name.
###############################################################################
macro (simptestcase2 testPkgDir testFileNameHead)
  add_test (
    NAME ${testPkgDir}/${testFileNameHead}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND ${SIMPTESTCASE} --m4 -v ${testPkgDir}/testcases/${testFileNameHead}.m4.simptestcase
    )
endmacro (simptestcase2)


###############################################################################
# Testcases
###############################################################################


simptestcase (usage-no-file-arguments)
simptestcase (invalid-arguments-file-does-not-exist)
simptestcase (multiple-file-arguments)

simptestcase (parse/ignored-lines)
simptestcase (parse/invalid-instruction-name)
simptestcase (parse/invalid-line-syntax)
simptestcase (parse/instruction-name-variants)

simptestcase (comments-blanklines-single-print)

simptestcase2 (print simple-print)
simptestcase2 (print suppress-print-output)

simptestcase (file-existing)
simptestcase (file-existing-relative-file-argument)
simptestcase (file-existing-with-suppress-non-path-output)
simptestcase (file-non-existing)

simptestcase2 (list existing-directory)
simptestcase2 (list existing-directory-relative-file-argument)
simptestcase2 (list wildcards)
simptestcase2 (list invalid-wildcard)
simptestcase2 (list directory-argument-missing)
simptestcase2 (list filer-on-filetype-file)
simptestcase2 (list filer-on-filetype-combined-with-namepattern)
simptestcase2 (list list-home-dir)
simptestcase2 (list sort)

simptestcase2 (include existing--relative-file-argument)
simptestcase2 (include existing-in-same-dir)
simptestcase2 (include existing-in-subdir)
simptestcase2 (include non-existing)
simptestcase2 (include existing-dir)
simptestcase2 (include inclusion-trace-in-error-messages)
simptestcase2 (include inclusion-trace-in-error-messages-file)

simptestcase2 (print-inclusion-hierarchy in-same-directory)
simptestcase2 (print-inclusion-hierarchy in-sub-directory)
simptestcase2 (print-inclusion-hierarchy in-same-directory-pretty)
simptestcase2 (print-inclusion-hierarchy in-sub-directory-pretty)
simptestcase2 (print-inclusion-hierarchy in-same-directory-multiple-args)

simptestcase2 (tags set-and-prepend)
simptestcase2 (tags set-and-append)
simptestcase2 (tags set-and-append-list)
simptestcase2 (tags include-export)
simptestcase2 (tags include-import)
simptestcase2 (tags filter)
simptestcase2 (tags filter-include)
simptestcase2 (tags filter-list)

simptestcase2 (other normalize-paths)
simptestcase2 (other normalize-paths-relative-file-argument)
simptestcase2 (other absolute-paths)
