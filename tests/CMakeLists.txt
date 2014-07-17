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
macro (testcase testPkgDir testFileNameHead)
  add_test (
    NAME ${testPkgDir}/${testFileNameHead}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND ${SIMPTESTCASE} --m4 -v ${testPkgDir}/testcases/${testFileNameHead}.m4.simptestcase
    )
endmacro (testcase)


###############################################################################
# Testcases
###############################################################################


testcase (basic invalid-arguments-file-does-not-exist)
testcase (basic comments-blanklines-single-print)
testcase (basic usage-no-file-arguments)
testcase (basic parse-ignored-lines)
testcase (basic parse-invalid-instruction-name)
testcase (basic parse-invalid-line-syntax)
testcase (basic simple-print)
testcase (basic suppress-print-output)
testcase (basic instruction-name-variants)
testcase (basic multiple-file-arguments)

testcase (file-path multiple-file-arguments)
testcase (file-path file-existing)
testcase (file-path file-existing-relative-file-argument)
testcase (file-path file-existing-with-suppress-non-path-output)
testcase (file-path file-non-existing)

testcase (list existing-directory)
testcase (list existing-directory-relative-file-argument)
testcase (list wildcards)
testcase (list invalid-wildcard)
testcase (list directory-argument-missing)
testcase (list filer-on-filetype-file)
testcase (list filer-on-filetype-combined-with-namepattern)
testcase (list list-home-dir)
testcase (list sort)

testcase (include existing--relative-file-argument)
testcase (include existing-in-same-dir)
testcase (include existing-in-subdir)
testcase (include non-existing)
testcase (include existing-dir)
testcase (include inclusion-trace-in-error-messages)
testcase (include inclusion-trace-in-error-messages-file)

testcase (print-inclusion-hierarchy in-same-directory)
testcase (print-inclusion-hierarchy in-sub-directory)
testcase (print-inclusion-hierarchy in-same-directory-pretty)
testcase (print-inclusion-hierarchy in-sub-directory-pretty)
testcase (print-inclusion-hierarchy in-same-directory-multiple-args)

testcase (tags set-and-prepend)
testcase (tags set-and-append)
testcase (tags set-and-append-list)
testcase (tags include-export)
testcase (tags include-import)
testcase (tags filter)
testcase (tags filter-include)
testcase (tags filter-list)
testcase (tags add)
testcase (tags remove)
testcase (tags invalid-command)

testcase (shell successful-command-in-same-dir-with-valid-output)
testcase (shell successful-command-in-same-dir-with-invalid-output)
testcase (shell unsuccessful-exit-command)
testcase (shell successful-command-in-sub-dir-with-valid-output)
testcase (shell tags-should-be-set)
testcase (shell tags-filter-included)
testcase (shell tags-filter-excluded)

testcase (preprocessor only-top-level-file)
testcase (preprocessor included-file)
testcase (preprocessor preprocessor-failure)

testcase (other normalize-paths)
testcase (other normalize-paths-relative-file-argument)
testcase (other output-absolute-paths)
