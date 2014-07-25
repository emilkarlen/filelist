###############################################################################
# Copyright 2014 Emil Karlén.
# 
# This file is part of filelist.
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

project(filelist/test NONE)


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
    NAME ${testPkgDir}::${testFileNameHead}
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
testcase (basic print--suppress-non-path-output)
testcase (basic instruction-name-variants)
testcase (basic multiple-file-arguments)
testcase (basic custom-instruction-prefix)

testcase (file-path multiple-file-arguments)
testcase (file-path existing)
testcase (file-path existing-relative-file-argument)
testcase (file-path existing-with-suppress-non-path-output)
testcase (file-path absolute-file-paths-existing)
testcase (file-path absolute-file-paths-existing-with-output-absolute-name)
testcase (file-path absolute-file-paths-nonexisting)

testcase (file-path/non-existing-files fail)
testcase (file-path/non-existing-files ignore)
testcase (file-path/non-existing-files include)
testcase (file-path/non-existing-files default-should-be-fail)

testcase (file-path/filter-on-tags contains-any-of)
testcase (file-path/filter-on-tags contains-any-of--alias--any-of)
testcase (file-path/filter-on-tags contains-none-of)
testcase (file-path/filter-on-tags contains-none-of--alias--none-of)
testcase (file-path/filter-on-tags proper-subset)
testcase (file-path/filter-on-tags subset)
testcase (file-path/filter-on-tags equals)
testcase (file-path/filter-on-tags equals--negated)
testcase (file-path/filter-on-tags equals--negated-2-times)
testcase (file-path/filter-on-tags equals--negated-3-times)
testcase (file-path/filter-on-tags proper-superset)
testcase (file-path/filter-on-tags superset)
testcase (file-path/filter-on-tags superset--negated)
testcase (file-path/filter-on-tags unequals)
# testcase (file-path/filter-on-tags command-line-parsing-of-empty-set)
# THE above test is not included due to ugly limitations of simptest.
testcase (file-path/filter-on-tags default-operator-is-contains-any-of)
testcase (file-path/filter-on-tags flexible-parsing-of-tag-list)

testcase (list existing-directory)
testcase (list existing-directory-absolute)
testcase (list existing-directory-relative-file-argument)
testcase (list directory-argument-missing)
testcase (list list-home-dir)
testcase (list sort)

testcase (list/file-condition name--include--shell-pattern)
testcase (list/file-condition name--include--shell-pattern--invalid)
testcase (list/file-condition name--include--reg-ex)
testcase (list/file-condition name--include--shell-pattern-and-regex)
testcase (list/file-condition name--exclude--shell-pattern)
testcase (list/file-condition type--file)
# testcase (list/file-condition name--exclude--reg-ex)
# testcase (list/file-condition combined--???) eller vad som nu ska göras??
testcase (list/file-condition combined--type-and-name)

testcase (include existing--relative-file-argument)
testcase (include existing-in-same-dir)
testcase (include existing-in-same-dir-absolute-filename)
testcase (include existing-in-subdir)
testcase (include non-existing)
testcase (include existing-dir)
testcase (include inclusion-trace-in-error-messages)
testcase (include inclusion-trace-in-error-messages-file)
testcase (include preserve-current-directory)

testcase (print-inclusion-hierarchy in-same-directory)
testcase (print-inclusion-hierarchy in-sub-directory)
testcase (print-inclusion-hierarchy in-same-directory-pretty)
testcase (print-inclusion-hierarchy in-sub-directory-pretty)
testcase (print-inclusion-hierarchy in-same-directory-multiple-args)
testcase (print-inclusion-hierarchy in-same-directory-multiple-args-pretty)

testcase (tags set-and-print)
testcase (tags set-and-prepend)
testcase (tags set-and-append)
testcase (tags set-and-append-list)
testcase (tags include-export--in-same-dir)
testcase (tags include-export--in-other-dir)
testcase (tags include-export-stack)
testcase (tags include-import--in-same-dir)
testcase (tags include-import--in-other-dir)
testcase (tags include-import-stack)
testcase (tags include-option-to-not-import-tags)
testcase (tags include-option-to-not-export-tags--stack--in-same-dir)
testcase (tags include-option-to-not-export-tags--stack--in-other-dir)
testcase (tags include-option-to-not-export-tags--current-tags--in-same-dir)
testcase (tags include-option-to-not-export-tags--current-tags--in-other-dir)
testcase (tags filter-include)
testcase (tags filter-list)
testcase (tags add)
testcase (tags remove)
testcase (tags invalid-command)
testcase (tags print-prefix-suffix)
testcase (tags print--suppress-non-path-output)
testcase (tags stack-push)
testcase (tags stack-pop-empty-stack)
testcase (tags stack-push-pop)
testcase (tags print-stack)
testcase (tags print-stack--suppress-non-path-output)

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

testcase (stdin-as-file-argument just-print)
testcase (stdin-as-file-argument allowed-at-most-once-on-command-line)
testcase (stdin-as-file-argument should-be-relative-cwd--file-path)
testcase (stdin-as-file-argument should-be-relative-cwd--other)
testcase (stdin-as-file-argument paths-relative-custom-dir)
testcase (stdin-as-file-argument preprocess)
testcase (stdin-as-file-argument print-inclusion-hierarchy)
testcase (stdin-as-file-argument print-inclusion-hierarchy--relative-custom-dir)
