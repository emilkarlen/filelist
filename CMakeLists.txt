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
# set (filelist_VERSION_MAJOR 1)
# set (filelist_VERSION_MINOR 0)

# set (CMAKE_INSTALL_PREFIX /home/karlen/tmp/test-install/${CMAKE_PROJECT_NAME})

find_program(PYTHON python3)

install(PROGRAMS src/filelist DESTINATION bin)


###############################################################################
# - build a CPack driven installer package -
###############################################################################


# include (InstallRequiredSystemLibraries)
# set (CPACK_RESOURCE_FILE_LICENSE  
#      "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
# set (CPACK_PACKAGE_VERSION_MAJOR "${filelist_VERSION_MAJOR}")
# set (CPACK_PACKAGE_VERSION_MINOR "${filelist_VERSION_MINOR}")
# include (CPack)


###############################################################################
# - test -
###############################################################################


enable_testing()

add_subdirectory(tests)
