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

project(filelist NONE)

# set (CMAKE_INSTALL_PREFIX /home/karlen/tmp/test-install/${CMAKE_PROJECT_NAME})

install(PROGRAMS src/filelist DESTINATION bin)


###############################################################################
# - test -
###############################################################################


enable_testing()

add_subdirectory(tests)
