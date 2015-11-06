###############################################################################
# Copyright 2014 Emil Karlén.
# 
# This file is part of filelist.
# 
# filelist is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# filelist is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with filelist.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

cmake_minimum_required(VERSION 2.8)

project(filelist/test NONE)

configure_file(
  common.m4.in
  ${CMAKE_CURRENT_SOURCE_DIR}/common.m4
) 

set (MAKE_EXECUTABLE ${PYTHON3} ${CMAKE_SOURCE_DIR}/tools/make-interpreted-executable.py)

macro (make_interpreted_program interpreter dir source target)
  set(target_file ${dir}/${target})
  set(source_file ${dir}/${source})
  add_custom_command (
    OUTPUT ${target_file}
    COMMAND ${MAKE_EXECUTABLE} --interpreter ${interpreter} --output ${target_file} --source ${source_file}
    DEPENDS ${source_file}
    )
  add_custom_target(
    test-executable-${target} ALL
    DEPENDS ${target_file}
    )
endmacro (make_interpreted_program)

make_interpreted_program (${BASH} ${CMAKE_CURRENT_SOURCE_DIR}/scripts simptestcase.bash simptestcase)
make_interpreted_program (${BASH} ${CMAKE_CURRENT_SOURCE_DIR}/scripts rename-simptestcase.bash rename-simptestcase)
make_interpreted_program (${PYTHON3} ${CMAKE_CURRENT_SOURCE_DIR}/scripts add-txt-suffix-to-file-paths.py add-txt-suffix-to-file-paths)
make_interpreted_program (${PYTHON3} ${CMAKE_CURRENT_SOURCE_DIR}/scripts shellcheck.py shellcheck)


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
    COMMAND bin/simptestcase --m4 -v packages/${testPkgDir}/testcases/${testFileNameHead}.m4.simptestcase
    )
endmacro (testcase)


macro (testcaseSC testPkgDir testFileNameHead)
  add_test (
    NAME SHELLCHECK/${testPkgDir}::${testFileNameHead}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMAND bin/shellcheck --preprocessor "m4 -P" packages/${testPkgDir}/testcases/${testFileNameHead}.shellcheckcase
    )
endmacro (testcaseSC)


###############################################################################
# Testcases
###############################################################################


testcaseSC (basic invalid-arguments-file-does-not-exist)
testcaseSC (basic comments-blanklines-single-print)
testcaseSC (basic usage-no-file-arguments)
testcaseSC (basic parse-ignored-lines)
testcaseSC (basic parse-invalid-instruction-name)
testcaseSC (basic parse-invalid-line-syntax)
testcaseSC (basic simple-print)
testcaseSC (basic print--suppress-non-path-output)
testcaseSC (basic instruction-name-variants)
testcaseSC (basic multiple-file-arguments)
testcaseSC (basic custom-instruction-prefix)


testcaseSC (file-path multiple-file-arguments)
testcaseSC (file-path existing)
testcaseSC (file-path existing-relative-file-argument)
testcaseSC (file-path existing-with-suppress-non-path-output)
testcaseSC (file-path absolute-file-paths-existing)
testcaseSC (file-path absolute-file-paths-existing-with-output-absolute-name)
testcaseSC (file-path absolute-file-paths-nonexisting)

testcaseSC (file-path/path-output-variants normalize-paths)
testcaseSC (file-path/path-output-variants normalize-paths-relative-file-argument)
testcaseSC (file-path/path-output-variants output-absolute-paths)


testcaseSC (file-path/non-existing-files fail)
testcaseSC (file-path/non-existing-files ignore)
testcaseSC (file-path/non-existing-files include)
testcaseSC (file-path/non-existing-files only)
testcaseSC (file-path/non-existing-files default-should-be-fail)

testcaseSC (file-path/filter-on-tags contains-any-of)
testcaseSC (file-path/filter-on-tags contains-any-of--alias--any-of)
testcaseSC (file-path/filter-on-tags contains-none-of)
testcaseSC (file-path/filter-on-tags contains-none-of--alias--none-of)
testcaseSC (file-path/filter-on-tags proper-subset)
testcaseSC (file-path/filter-on-tags subset)
testcaseSC (file-path/filter-on-tags equals)
testcaseSC (file-path/filter-on-tags equals--negated)
testcaseSC (file-path/filter-on-tags equals--negated-2-times)
testcaseSC (file-path/filter-on-tags equals--negated-3-times)
testcaseSC (file-path/filter-on-tags proper-superset)
testcaseSC (file-path/filter-on-tags superset)
testcaseSC (file-path/filter-on-tags superset--negated)
testcaseSC (file-path/filter-on-tags unequals)
# testcase (file-path/filter-on-tags command-line-parsing-of-empty-set)
# THE above test is not included due to ugly limitations of simptest.
testcaseSC (file-path/filter-on-tags default-operator-is-contains-any-of)
testcaseSC (file-path/filter-on-tags flexible-parsing-of-tag-list)


testcaseSC (list/existing-directory basic)
testcaseSC (list/existing-directory absolute)
testcaseSC (list/existing-directory relative-file-argument)

testcaseSC (list directory-argument-missing)
testcaseSC (list list-same-dir)
testcaseSC (list sort)

testcase (list/file-condition name--include--shell-pattern)
testcase (list/file-condition name--include--shell-pattern--invalid)
testcase (list/file-condition name--include--regex)
testcase (list/file-condition name--include--shell-pattern-and-regex)
testcase (list/file-condition name--exclude--shell-pattern)
testcase (list/file-condition name--exclude--regex)
testcase (list/file-condition type--include)
testcase (list/file-condition excludes-have-precedence)
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
testcase (tags set-and-prepend-append)
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
testcase (tags/forward-to-file-arguments do-not-forward)
testcase (tags/forward-to-file-arguments do-forward)


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


testcase (stdin-as-file-argument just-print)
testcase (stdin-as-file-argument allowed-at-most-once-on-command-line)
testcase (stdin-as-file-argument should-be-relative-cwd--file-path)
testcase (stdin-as-file-argument should-be-relative-cwd--other)
testcase (stdin-as-file-argument paths-relative-custom-dir)
testcase (stdin-as-file-argument preprocess)
testcase (stdin-as-file-argument print-inclusion-hierarchy)
testcase (stdin-as-file-argument print-inclusion-hierarchy--relative-custom-dir)
