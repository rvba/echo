#!/usr/bin/python

##########################################################################
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

import sys
import time
import platform
import os
from ctypes import *
import threading 
import mmap
import getpass 

##########################################################################
## Util  #################################################################
##########################################################################

debug = False
debug_geometry = False
debug_func = False
debug_version = True
debug_add = False
debug_update = False
debug_imported = False

## Convert strings (py2) to bytes (py3)
def to_bytes(string):
	if(sys.version_info[0] == 2):
		return string
	else:
		return bytes(string,"utf-8")

## True if used within a Python 3 environment
def is_py3():
	if(sys.version_info[0] == 2): return False
	else: return True

def to_string(data):
	if(sys.version_info[0] == 2):
		return data
	else:
		if isinstance(data,str): return data
		else: return data.decode("utf-8")

def to_int(data):
	if(sys.version_info[0] == 2):
		return int(data)
	else:
		return int.from_bytes(data, byteorder='little')

def get_platform_path():

	user = getpass.getuser()

	if os.name == 'nt':
		#path="C:\\Users\\" + user + "\\AppData\\Local\\Temp\\"
		path="C:\\Temp\\"
	else:
		path = "/tmp/"

	return path

def log(msg): print("[echo_pyhton] ",msg)

##########################################################################
## Library ###############################################################
##########################################################################

if os.name == 'nt':
	if platform.architecture()[0] == '64bit':
		arch = 64
		if os.path.dirname(__file__) == "":
			path = "\\..\\echo\\libecho64.dll"
		else:
			path = os.path.dirname(__file__) + "\\..\\echo\\libecho64.dll"
	else:
		arch = 32
		path = os.path.dirname(__file__) + "\\libecho32.dll"

else:
	file_path = os.path.dirname(__file__) 
	if platform.architecture()[0] == '64bit':
		arch = 64 
		if file_path != "":
			path = os.path.dirname(__file__) + "/../echo/libecho64.so"
		else:
			path = "../echo/libecho64.so"
	else:
		arch = 32
		if file_path != "":
			path = os.path.dirname(__file__) + "/libecho32.so"
		else:
			path = "libecho32.so"

r = cdll.LoadLibrary(path)  

if arch == 32:
	c_egreal = c_float
else:
	c_egreal = c_double

VNodeOwner = c_int

VN_OWNER_OTHER = 0
VN_OWNER_MINE = 1

init = r.ec_api_init


lock_ask = r.ec_api_lock_ask
lock_ask.restype = None

lock_use = r.ec_api_lock_use
lock_use.restype = c_int

lock_get = r.ec_api_lock_get
lock_get.restype = c_int

lock_release = r.ec_api_lock_release
lock_release.restype = None

connect = r.ec_api_connect
connect.argtypes = [c_char_p,c_char_p]
connect.restype = None

disconnect = r.ec_api_disconnect
disconnect.argtypes = [c_char_p]
disconnect.restype = None

update = r.ec_api_update

mesh_add = r.ec_api_mesh_add
mesh_add.argtypes = [ c_char_p ]
mesh_add.restype = c_int

mesh_vertex_set = r.ec_api_mesh_vertex_set
mesh_vertex_set.argtypes = [ c_int, c_int, c_double, c_double,c_double ]
mesh_vertex_set.restype = None

mesh_vertex_delete = r.ec_api_mesh_vertex_delete
mesh_vertex_delete.argtypes = [ c_int, c_int ]
mesh_vertex_delete.restype = None

object_position_set = r.ec_api_object_position_set
object_position_set.argtypes = [ c_int, c_float, c_float, c_float ]
object_position_set.restype = None

mesh_vertex_add = r.ec_api_mesh_vertex_add
mesh_vertex_add.argtypes = [ c_int, c_double, c_double, c_double ]
mesh_vertex_add.restype = None

mesh_face_set = r.ec_api_mesh_face_set
mesh_face_set.argtypes = [ c_int, c_int, c_int, c_int, c_int ]
mesh_face_set.restype = None

mesh_face_delete = r.ec_api_mesh_face_delete
mesh_face_delete.argtypes = [ c_int, c_int ]
mesh_face_delete.restype = None

mesh_face_add = r.ec_api_mesh_face_add
mesh_face_add.argtypes = [ c_int, c_int, c_int, c_int ]
mesh_face_add.restype = None

mesh_push = r.ec_api_mesh_push
mesh_push.argtypes = [ c_int ]
mesh_push.restype = None

object_add = r.ec_api_object_add
object_add.argtypes = [ c_char_p ]
object_add.restype = c_int

object_link = r.ec_api_object_link_push
object_link.argtypes = [ c_int, c_int ]
object_link.restype = None

object_push = r.ec_api_object_push
object_push.argtypes = [ c_int ]
object_push.restype = None

unhook = r.ec_api_unhook
unhook.restype = c_int 

get_object_id = r.ec_api_object_get_id
get_object_id.argtypes = [ c_int ]
get_object_id.restype = c_int 

get_echo_id = r.ec_api_object_get_echo_id
get_echo_id.argtypes = [ c_int ]
get_echo_id.restype = c_int

get_object_count = r.ec_api_object_node_get_count
get_object_count.restype = c_int

get_object_next = r.ec_api_object_node_get_next
get_object_next.argtypes = [ c_int ] 
get_object_next.restype = c_int

get_object_pos = r.ec_api_get_object_position
get_object_pos.argtypes = [ c_int ]
get_object_pos.restype = POINTER(c_double)

get_object_visibility = r.ec_api_get_object_visibility
get_object_visibility.argtypes = [ c_int ]
get_object_visibility.restype = c_int 

show_objects = r.ec_show_objects

get_mesh_object = r.ec_get_mesh_object
get_mesh_object.argtypes = [ c_int ] 
get_mesh_object.restype = c_int

get_mesh_vertices = r.ec_api_get_mesh_vertices
get_mesh_vertices.argtypes = [ c_int ]
get_mesh_vertices.restype = POINTER(c_egreal)

get_mesh_vertex_count = r.ec_api_get_mesh_vertex_count
get_mesh_vertex_count.argtypes = [ c_int ]
get_mesh_vertex_count.restype = c_int

get_mesh_faces = r.ec_api_get_mesh_faces
get_mesh_faces.argtypes = [ c_int ]
get_mesh_faces.restype = POINTER(c_int)

get_mesh_face_count = r.ec_api_get_mesh_face_count
get_mesh_face_count.argtypes = [ c_int ]
get_mesh_face_count.restype = c_int

get_links_count = r.ec_api_object_node_get_links_count
get_links_count.argtypes = [ c_int ]
get_links_count.restype = c_int

get_link_name = r.ec_api_object_node_get_link_name
get_link_name.argtypes = [ c_int, c_int ]
get_link_name.restype = c_char_p

get_mesh_version = r.ec_api_get_node_version_data
get_mesh_version.argtypes = [ c_int ]
get_mesh_version.restype = c_int

get_node_owner = r.ec_api_get_node_owner
get_node_owner.argtypes = [ c_int ]
get_node_owner.restype = c_int

get_node_name = r.ec_api_get_node_name
get_node_name.argtypes = [ c_int ]
get_node_name.restype = c_char_p

tag_group_create = r.ec_api_tag_group_create
tag_group_create.argtypes = [ c_int, c_int, c_char_p ]
tag_group_create.restype = c_int

tag_create_int = r.ec_api_tag_create_int
tag_create_int.argtypes = [ c_int, c_int, c_int, c_char_p, c_int, c_int ] 
tag_create_int.restype =  c_int 


##########################################################################
## Node     ##############################################################
##########################################################################

# A Verse Node
class Node:

	def __init__(self,id):
		self.id = id
		self.get_data()
		self.have_mesh = 0
		self.mesh = -1
		self.owner = -1
		self.name = "unknown"
		self.object = 0
		self.writed = False
		self.object_vertex_count = 0
		self.object_face_count = 0
		self.version = 0

	def has_object(self):
		if self.object != 0: return 1
		else: return 0

	# Get Mesh data
	def get_data(self):

		self.mesh = get_mesh_object(self.id)

		# wait for mesh node id
		if self.mesh > 0:
			self.vertex_count = get_mesh_vertex_count(self.mesh)
			self.vertices = cast(get_mesh_vertices(self.mesh),POINTER( c_egreal * 3 * self.vertex_count)).contents
			self.face_count = get_mesh_face_count(self.mesh)
			self.faces = cast(get_mesh_faces(self.mesh),POINTER( c_int * 4 * self.face_count)).contents
			self.mesh_version = get_mesh_version(self.mesh)
			self.owner = get_node_owner(self.mesh)
			self.name = get_node_name(self.id)
			self.have_mesh = 1

	# Show Node & Data
	def show(self):
		print("------------------------------------------------")
		print("[echo_python][show] object id:" + str(self.id) + " name:" +  to_string(self.name) + " version:" + str(self.version))
		if self.owner == -1:
			print("[echo_python][show] owner:not set")
		elif self.owner == VN_OWNER_MINE:
			print("[echo_python][show] owner","mine")
		else:
			print("[echo_python][show] owner","other")
		if self.mesh > 0:
			print("[echo_python][show] Mesh:",self.mesh)
			print("[echo_python][show] Vertex count:", self.vertex_count)

			for v in self.vertices:
				print("[echo_python][show] v:",v[0],v[1],v[2])

			print("[echo_python][show] Faces ", self.face_count)

			for f in self.faces:
				print("[echo_python] f:",f[0],f[1],f[2],f[3])

	# Store new node version and Return True  
	def check_version(self):
		if self.mesh == -1: self.get_data()
		if self.mesh > 0:
			version = get_mesh_version(self.mesh)
			if self.version != version:
				self.version = version
				return True
		return False

	# Bridge: write down to file
	def write(self):

		path = get_platform_path()

		# Update data (see blender -> add to echo.py)
		if self.mesh == -1: self.get_data()
		do_rebuild = False

		owner = self.owner 

		# Write down
		if self.mesh > 0 and self.writed == False and self.name != "unknown" and owner not in (-1,VN_OWNER_MINE):
			if self.have_mesh:
				self.writed = True

				version = get_mesh_version(self.mesh)
				self.version = version

				path_vertex = path + "rex_vertex_" + to_string(self.name) + ".txt"
				path_face = path + "rex_face_" + to_string(self.name) + ".txt"
				path_version = path + "rex_version_" + to_string(self.name) + ".txt"
				path_pos = path + "rex_pos_" + to_string(self.name) + ".txt"

				self.object_vertex_count = 0
				self.object_face_count = 0

				with open(path_pos,"w") as f:
					pos = cast(get_object_pos(self.id), POINTER(c_double * 3)).contents
					pos_str = str(pos[0]) + "," + str(pos[1]) + "," + str(pos[2]) 
					f.write(pos_str)
					f.close()

				with open(path_version,"w") as f:
					f.write(str(version))
					f.close()

				with open(path_vertex,"w") as f:
					count = 0
					for v in self.vertices:
						if is_py3():
							f.write(str(v[0]) + "," + str(v[1]) + "," + str(v[2]) + "\r\n")
						else:
							f.write(str(v[0]) + "," + str(v[1]) + "," + str(v[2]) + "\n")
						self.object_vertex_count = self.object_vertex_count + 1
						count = count + 1
					f.close()

				with open(path_face,"w") as f:

					for fa in self.faces:
						if is_py3():
							f.write(str(fa[0]) + "," +  str(fa[1]) + ","  + str(fa[2]) + "," + str(fa[3]) + "\n")
						else:
							f.write(str(fa[0]) + "," + str(fa[1]) + "," + str(fa[2]) + "," + str(fa[3]) + "\n")
						self.object_face_count = self.object_face_count + 1
					f.close()
						
		# Check for updates
		elif self.writed == True:

			v_vertex_count = get_mesh_vertex_count(self.mesh)
			v_face_count = get_mesh_face_count(self.mesh)

			# vertex count differs
			if self.object_vertex_count != v_vertex_count:
				self.writed = False

			# face count differs
			if self.object_face_count != v_face_count:
				self.writed = False

			# version differs
			version = get_mesh_version(self.mesh)
			if self.version != version:
				self.version = version
				if debug_version: print("[echo_pyhton] (write) New version:",version)
				self.get_data()
				self.writed = False


## Session  #################################################################
# Connect to server
# Store ids of distant nodes

class Session(threading.Thread):

	def __init__(self):

		# Threading
		threading.Thread.__init__(self)
		self.is_active = False
		self.is_thread_started = False
		# Node count
		self.max_objects = 10000
		self.objects_count = 0
		# Nodes 
		self.objects = [None] * self.max_objects 
		# Verse IDs
		self.objects_id = []
		# Lock
		self.lock_asked = False
		self.lock_use = lock_use()
		self.lock_have = False

	# Connection
	def connect(self,name,url):
		init()
		connect(to_bytes(name),to_bytes(url))

	def disconnect(self,msg):
		disconnect(to_bytes(msg))

	# Threading
	def run(self):
		self.is_thread_started = True
		self.live()

	def stop(self):
		self.is_active = False
		self.is_thread_started = False

	# Get list of ids
	def get_objects_id(self):
		
		count = get_object_count()
		objects_id = []
		obj = -1
		for i in range(count):
			obj = get_object_next(obj + 1)
			objects_id.append(obj)

		return objects_id

	# Get list of nodes
	def get_objects(self):

		lst = []
		for id in self.objects_id:
			obj = self.objects[id]
			lst.append(self.objects[id])
		return lst

	# Locks
	def _lock_get(self):
		if not self.lock_asked:
			self.lock_asked = True
			lock_ask()
			return False
		else:
			get = lock_get()
			return get

	def lock_release(self):
		self.lock_asked = False
		lock_release()

	# Session update
	def update(self):

		if debug_func: print("[echo_python] update (echo object)")

		do_update = True

		# Use lock
		if self.lock_use and not self.lock_have:
			do_update = False
			update()
			if self._lock_get():
				do_update = True
				self.lock_have = True
		# Update
		if do_update:

			# Update C Echo objects (push/pull)
			update(); 

			# Get current ids on server
			ids = self.get_objects_id()
			
			# For each id
			for id in ids:

				# Add New Echo Objects if slot is empty 
				if self.objects[id] == None:

					if self.objects_count < self.max_objects:

						# New Node 
						obj = Node(id)

						self.objects[obj.id] = obj
						self.objects_count = self.objects_count + 1
						self.objects_id.append(id)

						if debug_add: 
							print("[echo_python] Added new object id:" + str(id) + " name:" + str(get_node_name(id)))
							if debug_geometry: obj.show()
					else:
						if debug: print("[echo_python] Too many objects!")

			# Use Lock
			if self.lock_use:
				self.lock_release()
				self.lock_have= False

	# Show nodes
	def show(self):
		for id in self.objects_id:
			obj = self.objects[id]
			obj.show()

	def show_updates(self):
		for id in self.objects_id:
			obj = self.objects[id]
			if obj.check_version():
				obj.get_data()
				obj.show()

	# Bridge: clear files
	def clear_files(self):

		path = get_platform_path()
		files = os.listdir(path)
		
		for f in files:
			if f.startswith("rex_"):
				_f = path + f
				os.remove(_f)

		for f in files:
			if f.startswith("ec_"):
				_f = path + f
				os.remove(_f)

	# Bridge: write nodes
	def write_nodes(self):

		for id in self.objects_id:
			obj = self.objects[id]
			obj.write()


## STANDALONE  #################################################################

version=0
node_init = False
sent_done = 0
# Mesh and Object
m = None
o = None
tag = None
msg_err_file = False
msg_init = True

nodes = {}

def add_node(name,version,object,mesh):
	print("[echo_python] add node", name, "object", object, "mesh", mesh)
	nodes[name] =  {
			"name":name,
			"version":version,
			"object":object,
			"mesh":mesh,
			}

def get_node(name):
	global nodes
	if name in nodes:
		return nodes[name]
	else:
		return None



def msg_init():
	global msg_err_file
	if msg_err_file:
		msg_err_file = False
		log("No files found")

def update_tags():

	global tag,sent_done
	if o != None and sent_done == 0 and tag != None:
		#Tag
		id_verse = get_object_id( o)
		if id_verse != -1:
			if debug:print("[echo_pyhton] create tag:", tag)
			tag_group_create( id_verse,0,to_bytes("data"))
			tag_create_int( id_verse,0,0,to_bytes(tag),1,0) # 1 uiint32
			sent_done = 1

def parse_data(name):

	path = get_platform_path()
	vertex_path = path + "ec_vertex_" + name + ".txt"
	face_path = path + "ec_faces_" + name + ".txt"
	version_path = path + "ec_version_" + name + ".txt"
	tag_path = path + "ec_tag.txt_" + name + ".txt"
	pos_path = path + "ec_pos.txt_" + name + ".txt"

	#################################
	# Check for updates
	#################################
	# New version found

	node = get_node(name)

	# Init Node
	#################################
	if not node:
		print("[echo_python] Init node", name)

		tag = None
		version = 0

		# Tag File
		if(os.path.isfile(tag_path)):
			with open(tag_path,"r+b") as f:
				if not is_py3():
					map = mmap.mmap(f.fileno(), 0 )
					for line in iter(map.readline,""):
						line = str(line)
						line.rstrip('\r\n')
						tag = line 
				else:
					line = f.readline()
					line = to_string(line)
					tag = line 
					f.close()
		else:
			files_found = False

		# Version File
		if(os.path.isfile(version_path)):
			with open(version_path,"r+b") as f:
				if not is_py3():
					map = mmap.mmap(f.fileno(), 0 )
					for line in iter(map.readline,""):	
						line = to_string(line)
						line.rstrip('\r\n')
						if line != "":
							val = int(line)
							if version != val:
								version = val
								do_update = True
				else:
					line = f.readline()
					line = to_string(line)
					line.rstrip('\r\n')
					if line != '':
						val = int(line)
						if version != val:
							if debug_version: print("[echo_python] (parse) new version:",val)
							version = val
							# do update
							do_update = True
				f.close()
		else:
			files_found = False

		# [Create] Mesh and Object Nodes
		m = mesh_add(to_bytes(name))
		o = object_add(to_bytes(name))

		# Position
		if(os.path.isfile(pos_path)):
			with open(pos_path,"r+b") as f:
				for line in f:
					line = to_string(line)
					line.strip('\r\n')
					l = line.split(',')
					x = float(l[0])
					y = float(l[1])
					z = float(l[2])
					object_position_set(o,x,y,z)
				f.close()

		# Vertices
		if(os.path.isfile(vertex_path)):
			with open(vertex_path,"r+b") as f:

				if not is_py3():
					map = mmap.mmap(f.fileno(), 0 )
					for line in iter(map.readline,""):
						line = to_string(line)
						line.rstrip('\r\n')
						l = line.split(',')
						if len(l) >= 3:
							x = float(l[0])
							y = float(l[1])
							z = float(l[2])
							mesh_vertex_add(m,x,y,z)
				else:
					for line in f:
						line = to_string(line)
						line.rstrip('\r\n')
						l = line.split(',')
						if len(l) >= 3:
							x = float(l[0])
							y = float(l[1])
							z = float(l[2])
							mesh_vertex_add(m,x,y,z)	
				f.close()
		else:
			files_found = False

		# Faces
		if(os.path.isfile(face_path)):
			with open(face_path,"r+b") as f:

				if not is_py3():
					map = mmap.mmap(f.fileno(), 0 )
					for line in iter(map.readline,""):
						line.rstrip('\r\n')
						l = line.split(',')
						A = int(l[0])
						B = int(l[1])
						C = int(l[2])
						D = int(l[3])
						mesh_face_add(m,A,B,C,D)
				else:
					for line in f:
						line = to_string(line)
						line.rstrip('\r\n')
						l = line.split(',')
						A = int(l[0])
						B = int(l[1])
						C = int(l[2])
						D = int(l[3])
						mesh_face_add(m,A,B,C,D)


				f.close()
		else:
			files_found = False
	
		# Create Nodes
		mesh_push(m)
		object_link(o,m)
		object_push(o)

		# Debug
		if not files_found: msg_init()

		add_node(name,version,o,m)

	# Update Node
	##############################
	else:
		node = get_node(name)
		if not node: 
			print("[echo_python] null node")
			return 

		version = node["version"]
		m = node["mesh"]
		o = node["object"]

		if debug: print("SENDING NEW VERSION " + str(version))

		do_update = False

		# Version File
		if(os.path.isfile(version_path)):
			with open(version_path,"r+b") as f:
				if not is_py3():
					map = mmap.mmap(f.fileno(), 0 )
					for line in iter(map.readline,""):	
						line = to_string(line)
						line.rstrip('\r\n')
						if line != "":
							val = int(line)
							if version != val:
								version = val
								do_update = True
				else:
					line = f.readline()
					line = to_string(line)
					line.rstrip('\r\n')
					if line != '':
						val = int(line)
						if version != val:
							if debug_version: print("[echo_python] new version:",val,"/",version)
							version = val
							node["version"] = val
							# set update
							do_update = True
				f.close()
		else:
			files_found = False

		# Update if new version
		if do_update:

			if debug_update: print("[echo_python] UPDATE")

			# VERTICES
			if(os.path.isfile(vertex_path)):
				with open(vertex_path,"r+b") as f:

					#
					id_echo = get_object_id(o)
					mesh = get_mesh_object(id_echo)
					# en doublon ....
					distant_count = get_mesh_vertex_count(mesh)
					local_count = 0

					if not is_py3():
						map = mmap.mmap(f.fileno(), 0 )
						i = 0
						id_echo = get_object_id(o)
						mesh = get_mesh_object(id_echo)
						for line in iter(map.readline,""):
							line.rstrip('\r\n')
							l = line.split(',')
							x = float(l[0])
							y = float(l[1])
							z = float(l[2])
							mesh_vertex_set(mesh,i,x,y,z)
							local_count = local_count + 1
							i = i + 1
					else:
						i = 0
						id_echo = get_object_id(o)
						mesh = get_mesh_object(id_echo)
						for line in f:
							line = to_string(line)
							line.rstrip('\r\n')
							l = line.split(',')
							if len(l) == 3:
								x = float(l[0])
								y = float(l[1])
								z = float(l[2])
								mesh_vertex_set(mesh,i,x,y,z)
								local_count = local_count + 1
								i = i + 1
						

					f.close()

					if local_count < distant_count:
						if debug_update: print("[echo_python] DEL Vertices","local",local_count,"distant",distant_count)
						diff = distant_count - local_count
						for i in range(local_count, local_count + diff):
							mesh_vertex_delete(mesh,i)


			# FACES
			if(os.path.isfile(face_path)):
				with open(face_path,"r+b") as f:

					i = 0
					id_echo = get_object_id(o)
					mesh = get_mesh_object(id_echo)
					#
					distant_count = get_mesh_face_count(mesh)
					local_count = 0
						
					for line in f:
						line = to_string(line)
						line.rstrip('\r\n')
						l = line.split(',')
						if len(l) == 4:
							A = int(l[0])
							B = int(l[1])
							C = int(l[2])
							D = int(l[3])
							mesh_face_set(mesh,i,A,B,C,D)
							i = i + 1 

						# no tris ?
						local_count = local_count + 1

					f.close()

					if debug_update: print("[echo_python] Exported " + str(local_count) + " faces" )

					if local_count < distant_count:
						if debug_update: print("[echo_python] DEL Faces","local",local_count,"distant",distant_count)
						diff = distant_count - local_count
						for i in range(local_count, local_count + diff):
							mesh_face_delete(mesh,i)


			# Position 
			if(os.path.isfile(pos_path)):
				with open(pos_path,"r+b") as f:
					for line in f:
						line = to_string(line)
						line.strip('\r\n')
						l = line.split(',')
						x = float(l[0])
						y = float(l[1])
						z = float(l[2])
						object_position_set(o,x,y,z)
					f.close()


# [unused] Grab all rex_files (from server)
def get_all_names(names):

	path = get_platform_path()
	files = os.listdir(path)

	for f in files:
		if f.startswith("rex_vertex_"):
			spl = f.split('_')
			name = spl[2]
			n = name.split(".")
			_n = n[0]
			names.append(_n)

# Read ec_files and push (to server) 
def parse(session):

	path = get_platform_path()
	files = os.listdir(path)
	
	for f in files:
		if f.startswith("ec_vertex_"):
			spl = f.split('_')
			name = spl[2]
			n = name.split(".")
			_n = n[0]
			parse_data(_n)


# Read/Write to file
def bridge(url):

	print("[echo_python] Bridge mode")

	# Init echo (C)
	init()

	# New session
	connect(to_bytes("python"),to_bytes(url))
	loop = True
	session = Session()

	# Remove old files
	session.clear_files()

	while loop:

		# Echo
		update() 
		# Session
		session.update()
		# Read files and push Nodes to server
		parse(session)
		# Flush
		sys.stdout.flush()
		# Tags
		update_tags()
		# Write Nodes to file from server
		session.write_nodes()
		#session.show_updates()
		# Sleep	
		time.sleep(1/10)


if __name__ == '__main__':
	for arg in sys.argv:
		if arg in ['client','server','anim']:
			import test.test.py as test
			test.test(arg)
		elif arg == "bridge":
			if len(sys.argv) < 3:
				print("usage: echo.py bridge [url]")
			else:
				bridge(sys.argv[2])
		else:
			print("client","server","anim","bridge")


# vim: set noet sts=8 sw=8 :
