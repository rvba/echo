##########################################################################
# ##### ECHO ########################
#
#  This file is a part of Echo, a free software 
#  released under the GNU GPL Licence version 2
#  Copyright (C) 2018 Milovann Yanatchkov
#
# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
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
##########################################################################

import bpy
import os
import sys

# Local Path
root_path,t = os.path.split(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0,root_path)
# Import Echo
import echo_python.echo as Echo

import time
import ctypes
import bmesh
import multiprocessing as M

##########################################################################

# Global Session
SESSION = None

# Debug
debug = False
debug_func = False  
debug_geometry = False
debug_build = False
debug_update = False
debug_create = False

# Use
use_object_update = True
use_mesh_update = True

# Options
use_timer = True
timer_speed = 1
use_threads = False
use_multiprocessing = False
use_file_export = True
PROCESS= None

##########################################################################

# File mode
def export_to_file(name,vertices,faces):

	tag = "empty"

	print("[echo_python] export",int(time.time()))

	path = Echo.get_platform_path()
	vertex_path = path + "ec_vertex_" + name + ".txt"
	face_path = path + "ec_face_" + name + ".txt"
	version_path = path + "ec_version_" + name + ".txt"
	tag_path = path + "ec_tag_" + name + ".txt"

	with open(tag_path,"w+b") as f:
		f.write(Echo.to_bytes(tag + '\r\n'))
		f.close()

	with open(version_path,"w+b") as f:
		f.write(Echo.to_bytes(str(int(time.time()))+'\r\n'))
		f.close()

	with open(vertex_path,"w+b") as f:
		for v in vertices:
			f.write(Echo.to_bytes(str(v[0]) + ',' + str(v[1]) + ',' + str(v[2]) + '\r\n'))
		f.close()

	with open(face_path,"w+b") as f:
		for face in faces:
			f.write(Echo.to_bytes( str(face[0]) + ',' + str(face[1]) + ',' + str(face[2]) + ',' + str(face[3]) + '\r\n'))
		f.close()

# Multiporcessing
def proc():
	global SESSION
	while 1:
		SESSION._live_()

##########################################################################
## Blender Object   ######################################################
##########################################################################

class Bobject:

	# Init
	def __init__(self,bl_object,vs_object,vs_geometry):

		# Blender object
		self.bl_object = bl_object
		# Blender Mesh
		self.bl_mesh = None
		# Position
		self.pos = [0,0,0]
		# Verse ids
		self.vs_object = vs_object
		self.vs_geometry = vs_geometry
		# Status 
		self.is_built = False
		self.send_rebuild = False
		# Owner
		self.owner = "None"

	# Receive vertex 
	def receive_vertex(self):

		if debug_func: print("[echo_blender] Receive vertex")

		# Node is mine: wait for mesh
		if(self.owner == "mine") and not self.vobj.have_mesh:
			self.vobj.mesh = Echo.get_mesh_object(self.vobj.id)
			self.vobj.have_mesh = 1
			self.vobj.mesh_version = 0
			self.is_built = 1
			self.bl_mesh = self.bl_object.data

		# Check for new Version
		if self.vobj.have_mesh and self.is_built:

			# FIXME : indices may have change
			# FIXME : test from sender if tri/quad have changed and sent a special tag
			new_version = Echo.get_mesh_version(self.vobj.mesh)
			if new_version != self.vobj.mesh_version:
				if(debug_update):
					print("[echo_blender] Version Old: " + str(self.vobj.mesh_version) + " New:" + str(new_version))
				# Store new version
				self.vobj.mesh_version = new_version
				# Send Rebuild
				self.send_rebuild = True

	# Rebuild
	def rebuild(self):
		if debug_func: print("rebuild")
		self.is_built = False
		self.build()

	# Build a new Blender object if node is distant
	def build(self):
		if debug_func: print("[echo_blender] Build Blender Object")

		# Check node have a Mesh ID (or) is not built 
		if self.vobj.mesh == -1 or self.is_built == False:

			# Get Mesh ID
			mesh = Echo.get_mesh_object(self.vobj.id)

			# Check Data 
			if mesh != -1:
				# Get Data (vertices,faces)
				self.vobj.get_data()

			# If ID 
			if (self.vobj.mesh != -1):

				# Get Vertex,Face count
				vobj_vertex_count = Echo.get_mesh_vertex_count(self.vobj.mesh)
				vobj_face_count = Echo.get_mesh_face_count(self.vobj.mesh)

				# Exit if 0 vert
				if vobj_vertex_count == 0 : return

				# Get Name
				name = Echo.to_string(Echo.get_node_name(self.vobj.id))

				# Debug
				if debug_build: print("[echo_blender] build mesh name:" + name + 
						" id:" + 
						str(self.vobj.id) +
						" vertex count:" + str(vobj_vertex_count) + 
						" face count:" + str(vobj_face_count))
				# Vertices
				vertex_count = vobj_vertex_count

				# Get Data
				vertices = ctypes.cast(Echo.get_mesh_vertices(self.vobj.mesh),ctypes.POINTER( Echo.c_egreal * 3 * vertex_count)).contents

				# Debug Geometry
				if vertices:
					if debug_geometry:
						print("[echo_blender] vertex count:" + str(vertex_count))
						for v in vertices:
							print("[echo_blender] v ",v[0],v[1],v[2])

				# Faces
				face_count = vobj_face_count
				list_faces = []
				if debug_geometry: print("[echo_blender] face count:" + str(face_count))

				if face_count > 0:

					faces = ctypes.cast(Echo.get_mesh_faces(self.vobj.mesh),ctypes.POINTER( Echo.c_int * 4 * face_count)).contents

					if faces:
						update = 0
						
						for f in faces:

							update = 1
							# Fill list_faces
							if f[3] != -1:
								if debug_geometry: print("[echo_blender] quad: ",f[0],f[1],f[2],f[3])
								list_faces.append((f[0],f[1],f[2],f[3]))
							else:
								if debug_geometry: print("[echo_blender] tri: ",f[0],f[1],f[2])
								list_faces.append((f[0],f[1],f[2]))


				# Vertices
				v = []
				for vec in vertices:
					# Fill v
					v.append((vec[0],vec[1],vec[2]))

				# New mesh
				me = bpy.data.meshes.new(name)
				me.from_pydata(v,[],list_faces)
				me.update()

				# New object
				if self.bl_object == None:
					ob = bpy.data.objects.new(name,me)
					self.bl_object = ob
					bpy.context.scene.objects.link(self.bl_object)

					# Not allowed! [1]
					#self.receive_pos()

				# Object already exists: change data
				else:
					self.bl_object.data = me

				# Remove old mesh
				if self.bl_mesh != None:
					bpy.data.meshes.remove(self.bl_mesh)
					me.name = name

				# Store new mesh
				self.bl_mesh = me

				# Set built
				self.is_built = True

	# Send vertex updates
	def send_vertex(self):
		if debug_func: print("send updates")

		#FIXME : can remove that if
		if self.bl_object.mode == 'EDIT':
			use_bmesh = 1
			if use_bmesh:
				try:
				#if True:
					_mesh = self.bl_object.data
					mesh = bmesh.from_edit_mesh(_mesh)
					selected_verts = [v for v in mesh.verts if v.select]
					for v in selected_verts:
						self.vobj.get_data()
						_id = self.vobj.mesh
						Echo.mesh_vertex_set( _id,v.index,v.co.x,v.co.y,v.co.z)
				except:
					pass
	# Send position
	def send_pos(self):
		if debug_func: print("send pos")

		vobj = self.vobj
		obj = self.bl_object
		if vobj != None and obj != None:
			id = self.vobj.id
			loc = self.bl_object.location
			Echo.object_position_set(id,loc.x,loc.y,loc.z)

			self.pos[0] = loc.x
			self.pos[1] = loc.y
			self.pos[2] = loc.z

	# Receive postion
	def receive_pos(self):
		if debug_func: print("[echo_blender] receive pos")
		pos = ctypes.cast( Echo.get_object_pos(self.vobj.id), ctypes.POINTER( ctypes.c_double * 3)).contents
		if pos:
			try:
				self.bl_object.location.x = pos[0]
				self.bl_object.location.y = pos[1]
				self.bl_object.location.z = pos[2]

				self.pos[0] = pos[0]
				self.pos[1] = pos[1]
				self.pos[2] = pos[2]
			except:
				pass

	# Update position
	def update_position(self):
		if debug_func: print("[echo_blender] check pos")

		# Send 
		if self.pos[0] != self.bl_object.location.x or self.pos[1] != self.bl_object.location.y or self.pos[2] != self.bl_object.location.z:
			self.send_pos()
		# Receive
		else:
			# updated every time
			# FIXME: sould check verse version if exists
			self.receive_pos()

	# Set visibility On/Off
	def check_visibility(self):
		if debug_func: print("[echo_blender] check visibilty")

		if Echo.get_object_visibility(self.vobj.id):
			self.bl_object.hide = True
		else:
			self.bl_object.hide = False

	# Sync Node and Object
	def update(self):
		if debug_func: print("[echo_blender] Object update")

		if self.bl_object != None:
			# Edit mode: send updates
			if self.bl_object.mode == 'EDIT':
				self.send_vertex()
			# Object mode
			else:
				# Rebuild
				if self.send_rebuild:
					self.send_rebuild = False
					self.rebuild()
				else:
					# Or receive updates
					if use_object_update:
						self.update_position()
						self.check_visibility()
					if use_mesh_update:
						self.receive_vertex()


##########################################################################
## Session   #############################################################
##########################################################################
# Bind Nodes and Blender objects
class Session(Echo.Session):

	def __init__(self):

		Echo.Session.__init__(self)

		self.debug = True
		self.objects_mine = [None] * self.max_objects 
		#self.objects_mine_file = [None] * self.max_objects 
		self.objects_mine_file = []  
		self.objects_mine_count = 0
		self.objects_other = []
		self.use_file = False

	def get_bl_obj_by_name(self,name):
		if debug_func: print("get_bl_obj_by_name")
		for obj in self.objects_mine_file:
			if name == obj.bl_object.name:
				return obj
		return None

	# Blender Objects
	def update_objects(self):
		if debug_func: print("[echo_blender] update blender nodes")

		# Get Verse nodes 
		objects = self.get_objects()

		# For each node
		for obj in objects:
				
			# Node is Mine : Bind node and blender object
			if Echo.get_node_owner(obj.id) == Echo.VN_OWNER_MINE:

				# Init: Bind node to Blender object
				if not obj.has_object():

					# By Name (File Mode)
					if self.use_file:
						object = self.get_bl_obj_by_name(obj.name)
						if object:
							obj.object = object
							obj.object.vobj = obj
						else:
							print("Cant find by name")
					# or

					# By Echo ID
					id_echo = Echo.get_echo_id(obj.id)
					# Grab Blender Object
					object = self.objects_mine[id_echo]
					if object != None:
						obj.object = object
						# FIXME: (self ref)
						obj.object.vobj = obj

				# Update
				else:
					obj.object.update()

			# Node is Other : Add a Blender object and update it
			else:
				# Update : If has Object.object: Build and Update 
				if obj.has_object():
					obj.object.build()
					obj.object.update()

				# Init : Add a new Object.object and wait for verse mesh
				else:
					if self.use_file:
						# Check it's not mine
						name = Echo.get_node_name(obj.id)
						if not name.startswith(b"node"):
							object = self.get_bl_obj_by_name(str(name))
							if object:
								obj.object = object
								obj.object.vobj = obj
					else:
						if debug_create: print("[echo_blender] Create new object id:",obj.id)
						# Add an Empty Blender Object
						obj.object = Bobject(None,None,None)
						# Store Verse ID
						obj.object.vobj = obj

	# Update (Main Call)
	def update(self):
		if debug_func: print("[echo_blender] update")

		# Get nodes from the server
		super().update()

		# Update Blender nodes 
		self.update_objects()

	# Main Loop (Threading) 
	def live(self):
		while 1:
			if self.is_active:
				self.update()
			else:
				return

	# Main Loop (Multiprocess)
	def _live_(self):
		self.update()

##########################################################################
## Operators #############################################################
##########################################################################

# Add a Blender Object to the Server
class Rev_add(bpy.types.Operator):

	"""Add object"""
	bl_idname = "echo.add"
	bl_label = 'Add object'
	bl_options = {'UNDO'}

	# Serialize Faces to List
	def make_faces(self,faces):

		lst = []
		for f in faces:
			face = []
			vcount = 0
			for v in f.vertices:
				face.append(v)
				vcount = vcount + 1

			# triangles
			if vcount == 3: face.append(-1) 
			lst.append(face)

		return lst

	# Serialize Vertices to List
	def make_vertices(self,vertices):

		lst = []
		for v in vertices:
			vert = []
			vert.append(v.co[0])
			vert.append(v.co[1])
			vert.append(v.co[2])
			lst.append(vert)

		return lst


	def execute(self, context):

		global SESSION

		if SESSION != None:

			for obj in bpy.context.selected_objects:

				if obj.type == 'MESH':

					vertices = obj.data.vertices
					faces = obj.data.polygons

					# If File Mode
					if context.scene.rev_use_file:
						print("use file")

						# Build Face/Vertice lists
						v = self.make_vertices(vertices)
						f = self.make_faces(faces)

						# Write to file 
						export_to_file(obj.name,v,f)

						# New node
						o = Bobject(obj,None,None)
						o.owner = "mine"

						# Store it for later binding
						SESSION.objects_mine_file.append(o)

						if debug: print("[echo_blender] Add Object ", object_id)

					# Regular Mode
					else:

						# Add Nodes
						mesh_id = Echo.mesh_add(Echo.to_bytes(obj.name))
						object_id = Echo.object_add(Echo.to_bytes(obj.name))

						# Add Vertices
						for v in vertices:
							Echo.mesh_vertex_add(mesh_id,v.co[0],v.co[1],v.co[2])

						# Add Faces
						for f in faces:
							vertices = f.vertices
							face = []
							i = 0
							for v in vertices:
								face.append(v)
								i = i + 1

							# triangles
							if i == 3: face.append(-1) 

							Echo.mesh_face_add(mesh_id,face[0],face[1],face[2],face[3])

						# Link
						Echo.object_link(object_id,mesh_id)

						# Push
						Echo.mesh_push(mesh_id)
						Echo.object_push(object_id)

						# New node
						o = Bobject(obj,object_id,mesh_id)
						o.owner = "mine"

						# Store it for later binding
						SESSION.objects_mine[object_id] = o 

						if debug: print("[echo_blender] Add Object ", object_id)


		return {'FINISHED'}

# Connect gui
class Session_connect(bpy.types.Operator):

	bl_idname = "echo.connect"
	bl_label = 'Start server'
	bl_options = {'UNDO'}

	inited = False
	_timer = False

	def init(self,context):

		# New session
		global SESSION
		SESSION = Session()

		if context.scene.rev_is_local:
			if debug: print("[echo_blender] connecting to localhost")
			SESSION.connect("blender","localhost")
		else:
			if debug: print("[echo_blender] connecting to " + context.scene.rev_url)
			SESSION.connect("blender",context.scene.rev_url)

		SESSION.is_active = True

		if context.scene.rev_use_file:
			print("USE FILE")
			SESSION.use_file = True

	def modal(self, context,event):

		if SESSION != None:
			if event.type == 'TIMER':
				# When it's time, update session
				SESSION.update()
			return {'PASS_THROUGH'}
		else:
			context.window_manager.event_timer_remove(self._timer)
			return {'FINISHED'}

	def invoke(self,context,event):

		# Threads
		if use_threads:
			self.init(context)
			if not SESSION.is_thread_started:
				SESSION.start()
				return {'FINISHED'}
		# Multiprocess
		elif use_multiprocessing:
			self.init(context)
			global PROCESS
			p = M.Process(target=proc)
			PROCESS = p
			p.start()
			return {'FINISHED'}
		# Modal
		else:
			if not self.inited:
				self.inited = True
				self.init(context)
				# add a timer
				self._timer = context.window_manager.event_timer_add(0.05, context.window)
				context.window_manager.modal_handler_add(self)
				return {'RUNNING_MODAL'}

# Connect console
class Session_connect_console(bpy.types.Operator):

	bl_idname = "echo.connect_console"
	bl_label = 'Start server'
	bl_options = {'UNDO'}

	inited = False
	_timer = False

	def init(self,context):

		global SESSION
		SESSION = Session()

		if context.scene.rev_is_local:
			if debug: print("[echo_blender] connecting to localhost")
			SESSION.connect("blender","localhost")
		else:
			if debug: print("[echo_blender] connecting to " + context.scene.rev_url)
			SESSION.connect("blender",context.scene.rev_url)

		SESSION.is_active = True

		if context.scene.rev_use_file:
			SESSION.use_file = True

	def modal(self,context,event):
		if event.type == 'TIMER':SESSION.update()


	def execute(self,context):
		use_threads = True
		if use_threads:
			self.init(context)
			if not SESSION.is_thread_started:
				SESSION.start()
		elif use_multiprocessing:
			self.init(context)
			global PROCESS
			p = M.Process(target=proc)
			PROCESS = p
			p.start()
		else:
			if not self.inited:
				self.inited = True
				self.init(context)

			if SESSION != None:
				if use_timer:
					context.window_manager.event_timer_add(timer_speed,context.window)
					context.window_manager.modal_handler_add(self)
				else:
					if event.type == 'TIMER':
						SESSION.update()
					return {'PASS_THROUGH'}
			else:
				context.window_manager.event_timer_remove(self._timer)
				return {'FINISHED'}

		return {'RUNNING_MODAL'}



# Disconnect
class Session_disconnect(bpy.types.Operator):

	bl_idname = "echo.disconnect"
	bl_label = 'Stop server'
	bl_options = {'UNDO'}

	def execute(self, context):

		global SESSION

		SESSION.disconnect("leaving")

		if use_threads:
			SESSION.stop()
		elif use_multiprocessing:
			PROCESS.terminate()
		else:
			SESSION.stop()
			
		SESSION = None

		return {'FINISHED'}


# Main Panel
class Rev_panel(bpy.types.Panel):

	bl_space_type='PROPERTIES'
	bl_region_type='WINDOW'
	bl_context="scene"
	bl_label="Echo"

	bpy.types.Scene.rev_is_local = bpy.props.BoolProperty("rev_is_local", default=True)
	bpy.types.Scene.rev_use_file = bpy.props.BoolProperty("rev_use_file", default=False)
	bpy.types.Scene.rev_connect = bpy.props.BoolProperty("rev_connect", default=False)
	bpy.types.Scene.rev_url = bpy.props.StringProperty("rev_url", default="192.168.0.21")

	@classmethod
	def poll(cls,context):
		return context.scene

	def draw(self,context):

		global SESSION

		scene = bpy.context.scene
		layout=self.layout
		col=layout.column(align=True)
		if SESSION != None:
			col.operator(Session_disconnect.bl_idname,text="Disconnect")
		else:
			col.operator(Session_connect.bl_idname,text="Connect")

		col=layout.column(align=True)
		if scene.rev_is_local:
			col.prop(context.scene,"rev_is_local",text="Localhost",toggle=True)
		else:
			col.prop(context.scene,"rev_is_local",text="url",toggle=True)
			col.prop(context.scene,"rev_url",text="")
		col.prop(context.scene,"rev_use_file",text="Use file",toggle=True)

		col=layout.column(align=True)
		if SESSION!= None:
			col.operator(Rev_add.bl_idname,text="Add")


# vim: set noet sts=8 sw=8 :
