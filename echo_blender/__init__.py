# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>


bl_info = {
		"name": "echo_blender",
		"author": "rvba",
		"blender": (2, 7, 9),
		"location": "Scene",
		"description": "Verse client",
		"wiki_url": "https://www.github.com/rvba/echo.git",
		"category": '',
		}

import imp

if "bpy" in locals():
	imp.reload(echo_blender)
else:
	from . import echo_blender 

import bpy

def register():
	bpy.utils.register_module(__name__)

def unregister():
	bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
	if "bpy" in locals():
		register()



# vim: set noet sts=8 sw=8 :
