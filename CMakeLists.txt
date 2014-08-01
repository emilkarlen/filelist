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

project(filelist NONE)

# The version number.
set (filelist_VERSION_MAJOR 1)
set (filelist_VERSION_MINOR 0)
set (filelist_VERSION_PATCH 0)

find_program(PYTHON3 python3)
find_program(BASH bash)
find_program(SED sed)
find_program(CP cp)
find_program(CHMOD chmod)

configure_file(
  src/filelist-header.txt.in
  ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist-header.txt
) 

add_custom_command(
  OUTPUT  ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist
  COMMAND ${CP} ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist-header.txt ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist
  COMMAND ${SED} '/BEGIN filelist-header/,/END filelist-header/d' ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist.py >> ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist
  COMMAND ${CHMOD} +x ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist.py
  COMMENT Building filelist
  )

add_custom_target(
  filelist-executable ALL
  DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist
  )

install(PROGRAMS ${CMAKE_CURRENT_SOURCE_DIR}/src/filelist DESTINATION bin)


###############################################################################
# - CPack configuration -
###############################################################################


set (CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")

set (CPACK_PACKAGE_VERSION_MAJOR "${filelist_VERSION_MAJOR}")
set (CPACK_PACKAGE_VERSION_MINOR "${filelist_VERSION_MINOR}")
set (CPACK_PACKAGE_VERSION_PATCH "${filelist_VERSION_PATCH}")

set (CPACK_SOURCE_IGNORE_FILES ".*~.*;\\\\.#.*;tmp/")
list (APPEND CPACK_SOURCE_IGNORE_FILES "/\\\\.git/")
list (APPEND CPACK_SOURCE_IGNORE_FILES "/\\\\.gitignore")
list (APPEND CPACK_SOURCE_IGNORE_FILES "/\\\\.idea/")
list (APPEND CPACK_SOURCE_IGNORE_FILES "/doc/")

include (CPack)


###############################################################################
# - test -
###############################################################################


enable_testing()

add_subdirectory(tests)
