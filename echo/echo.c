/* 
 * Copyright (C) 2018 Milovann Yanatchkov 
 *
 * This file is part of Echo , a free software
 * licensed under the GNU General Public License v2
 * see /LICENSE for more information
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <limits.h>

#include "verse.h"
#include "math.h"
#include "string.h"
#include "unistd.h"

#include "lst.h"
#include "stash.h"
#include "enough.h"
#include "umber.h"
#include "e_storage_node.h" 
#include "echo.h"

#define RENODE_READY 1
#define DISCONNECT_MSG_LENGTH 128

//#define DEBUG
//#define DEBUG_GEOMETRY

/* ************* Structs ******************/

typedef struct Session
{
	char name[NAME_SIZE];		/** Avatar name on the server */
	char hostname[NAME_SIZE];	/** localhost or distant URL of the verse server */
	int is_connected;		/** True when connected with the server */
	int has_avatar;			/** True when avatar name is set */

	t_lst *geometries;		/** List of Ec_Geometry */
	t_lst *objects;			/** List of Ec_Object */
	t_lst *pending_nodes;		/** List of pending nodes */
	t_lst *pending_links;		/** List of pending links */

	int unhook;			/** Use to disconnect from the server after all objects are pushed */

}t_session;

/* ************* Globals ******************/

static unsigned int vconnection;

t_ecnode *PENDING_NODE = NULL;
t_ecnode *PENDING_LINK = NULL;

t_session *SESSION = NULL;
t_lst *GEOMETRIES = NULL;
t_lst *OBJECTS = NULL;

int GEOMETRY_COUNT = 0;
int OBJECT_COUNT = 0;
int NODE_COUNT = 0;
int LOCK_USE = 0;
int LOCK_GET = 0;
int LOCK_SESSION = 1;
int LOCK_ASK = 0;
int LOCK_RELEASE = 0;
int USE_CHECKING = 1;
int DO_DISCONNECT = 0;
char DISCONNECT_MSG[DISCONNECT_MSG_LENGTH] = {0};

/* ************* Forward declarations  ******************/

t_ecnode *ec_node_add( t_session *session, int type, const char *name);
void ec_session_node_pop( t_session *session, int id);

/* ************* Enough   ******************/

typedef struct MeshNode
{
	uint id;
	uint version;
	egreal *vertices;
	uint *faces;
	uint vertex_count;
	uint face_count;

}t_meshnode;

t_meshnode *ec_meshnode_new( void)
{
	t_meshnode *node = ( t_meshnode *) calloc( 1, sizeof( t_meshnode));
	return node;
}

void ec_show_objects( void)
{
	ENode *node;
	for(node = e_ns_get_node_next(0, 0, V_NT_OBJECT); node != NULL; node = e_ns_get_node_next(e_ns_get_node_id(node) + 1, 0, V_NT_OBJECT))
	{
		char *name = e_ns_get_node_name(node);
		uint id=e_ns_get_node_id(node);
		printf("[echo] show object [Node (%s) id:%d]\n", name, id);
	}
}

t_meshnode *ec_get_mesh_meshnode( uint id)
{
	/* Get Node */
	ENode *node = e_ns_get_node( 0, id);

	if(node)
	{
		/* Get custom data */
		t_meshnode *meshnode = ( t_meshnode *) e_ns_get_custom_data( node, 1);

		/* Update data */
		if(meshnode->version != e_ns_get_node_version_data(node))
		{
			meshnode->version = e_ns_get_node_version_data(node);

			egreal *v = e_nsg_get_layer_data(node, e_nsg_get_layer_by_id(node, 0));
			uint *f = e_nsg_get_layer_data(node, e_nsg_get_layer_by_id(node, 1));
			uint vlength = e_nsg_get_vertex_length( node);
			uint flength= e_nsg_get_polygon_length( node);

			meshnode->vertices = v;
			meshnode->faces = f;

			uint i;
			meshnode->vertex_count = 0;
			for( i = 0; i < vlength; i++)
			{
				if( v[i*3] == V_REAL64_MAX) break;
				meshnode->vertex_count++;
				//printf("v%d: %f %f %f\n", i, v[i*3+0], v[i*3+1], v[i*3+2]);
			}

			meshnode->face_count = 0;
			for ( i = 0; i < flength; i++)
			{
				if(
					f[i * 4] < vlength &&
					f[i * 4 + 1] < vlength &&
					f[i * 4 + 2] < vlength &&
					v[f[i * 4] * 3] != V_REAL64_MAX &&
					v[f[i * 4 + 1] * 3] != V_REAL64_MAX &&
					v[f[i * 4 + 2] * 3] != V_REAL64_MAX)
				{
					meshnode->face_count++;
					//printf("f: %d %d %d %d\n", f[i*4+0], f[i*4+1], f[i*4+2], f[i*4+3]);
				}
				else
					break;
			}
		}

		/* needed */
		return meshnode;
	}
	else
	{
		return NULL;
	}
}

/* get id of object->link->mesh */
uint ec_get_mesh_object( uint id_object)
{
	uint id = -1;
	ENode *node = e_ns_get_node( 0, id_object);
	if( node)
	{

		ENode *g_node = NULL;
		EObjLink *link;

		for(link = e_nso_get_next_link(node, 0); link != NULL; link = e_nso_get_next_link(node, e_nso_get_link_id(link) + 1))
		{
			if(link)
			{
				if((g_node = e_ns_get_node(0, e_nso_get_link_node(link))) != NULL && V_NT_GEOMETRY == e_ns_get_node_type(g_node))
				{
					break;
				}
			}
		}

		if( g_node) id = e_ns_get_node_id( g_node);
	}

	return id;
}

/* API */

/* Set */

void ec_api_mesh_vertex_set( int id, int indice, double x, double y, double z)
{
	verse_send_g_vertex_set_xyz_real32( id, 0, indice ,x,y,z);
}

void ec_api_mesh_vertex_delete( int id, int indice)
{
	verse_send_g_vertex_delete_real32( id, indice);
}

void ec_api_mesh_face_set( int id, int indice, int a, int b, int c, int d)
{
	verse_send_g_polygon_set_corner_uint32( id, 1, indice, a, b, c, d);
}

void ec_api_mesh_face_delete( int id, int indice)
{
	verse_send_g_polygon_delete( id, indice);
}

void ec_api_object_position_set( int id, float x, float y, float z)
{
	float pos[] = {x,y,z};
	verse_send_o_transform_pos_real32( id, 0, 0, pos, NULL, NULL, NULL, 0);
}

/* Get Geometry */

int ec_api_object_link_get( int id)
{
	return 1;
}

uint ec_api_get_mesh_face_count( uint id)
{
	t_meshnode *n = ec_get_mesh_meshnode( id);
	if(n) return n->face_count;
	else return 0;
}

egreal *ec_api_get_mesh_vertices( uint id)
{
	t_meshnode *n = ec_get_mesh_meshnode( id);
	if(n) return n->vertices;
	else return 0;
}

uint *ec_api_get_mesh_faces( uint id)
{
	t_meshnode *n = ec_get_mesh_meshnode( id);
	if(n) return n->faces;
	else return 0;
}

uint ec_api_get_mesh_vertex_count( uint id)
{
	t_meshnode *n = ec_get_mesh_meshnode( id);
	if(n) return n->vertex_count;
	else return 0;
}

double *ec_api_get_object_position( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	static double pos[3];
	if( node)
	{
		e_nso_get_pos( node, pos, NULL, NULL, NULL, NULL, NULL);
	}
	return pos;
}

uint ec_api_get_object_visibility( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	if( node)
	{
		return e_nso_get_hide( node);
	}
	return 0;
}

uint ec_api_object_node_get_links_count( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	EObjLink *link;
	uint count = 0;
	if( node)
	{
		for( link = e_nso_get_next_link( node, 0) ; link; link = e_nso_get_next_link( node, e_nso_get_link_id( link) + 1 ))
		{
			count++;
		}
	}
	return count;
}

char *ec_api_object_node_get_link_name( uint node_id, uint link_id)
{
	ENode *node = e_ns_get_node( 0, node_id);
	if( node)
	{
		EObjLink *link = e_nso_get_link( node, link_id);
		return e_nso_get_link_name( link);
	}
	else
	{
		static char error[] = "not_found";
		return error;
	}
}

VNodeID ec_api_get_link_node( VNodeID node_id, uint link_id)
{
	ENode *node = e_ns_get_node( 0, node_id);
	if( node)
	{
		EObjLink *link = ( EObjLink *) e_nso_get_link( node, link_id);
		return e_nso_get_link_node( link);
	}
	else
	{
		return 0;
	}
}

/* Get Node */

uint ec_api_node_get_count( VNodeType type)
{
	return e_ns_get_node_count( 0, type);
}

uint ec_api_node_get_next( VNodeType type, uint id)
{
	ENode *node = e_ns_get_node_next( id, 0, type);
	if( node) return e_ns_get_node_id( node);
	else return -1;
}

uint ec_api_object_node_get_count( void)
{
	return e_ns_get_node_count( 0, V_NT_OBJECT);
}

uint ec_api_object_node_get_next( uint id) /* starts at 0 */
{
	ENode *node = e_ns_get_node_next( id, 0, V_NT_OBJECT);
	if( node) return e_ns_get_node_id( node);
	else return -1;
}

char *ec_api_get_node_name( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	if( node) return e_ns_get_node_name( node);
	else 
	{
		static char error[] = "not_found";
		return error;
	}
}

uint ec_api_get_node_version_data( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	if( node) return e_ns_get_node_version_data(node);
	else return 0;
}

uint ec_api_get_node_owner( uint id)
{
	ENode *node = e_ns_get_node( 0, id);
	if( node) return e_ns_get_node_owner( node);
	else return 0;
}

/* Callback */

/* Custom geometry func 
 * Links Enode and Mesh node
 * */

void ec_node_geometry(ENode *node, ECustomDataCommand command)
{
	if(command == E_CDC_CREATE)
	{
		/* Create a new meshnode */
		t_meshnode *meshnode = ec_meshnode_new();
		/* as a node custom data */
		e_ns_set_custom_data(node, 1, meshnode);
	}

	//if(command == E_CDC_DESTROY)
}

/* ************* Util  ******************/

const char *ec_print_type( int type)
{
	switch( type)
	{
		case V_NT_OBJECT: return "object"; break;
		case V_NT_GEOMETRY: return "geometry"; break;
		default: return "unkown"; break;
	}
}

void ec_node_show( t_ecnode *node)
{
	printf(" [echo] name:%s type:%s ec_id:%d id:%d\n", node->name, ec_print_type(node->type), node->ec_id, node->id);
}

void ec_pending_show( void)
{
	printf("[echo] pending_nodes: \n");
	t_link *l;
	t_lst *lst = SESSION->pending_nodes;
	for(l=lst->first;l;l=l->next)
	{
		t_ecnode *node = ( t_ecnode *) l->data;
		ec_node_show( node);
	}
}

/* ************* Objects ******************/

t_ecobject *ec_object_new( void)
{
	t_ecobject *object = ( t_ecobject *) calloc( 1, sizeof( t_ecobject));
	return object;
}

t_ecobject *ec_object_add( t_session *session, const char *name)
{
	t_ecnode *node = ec_node_add( session, V_NT_OBJECT, name);
	t_ecobject *object = ec_object_new();
	node->data = object;
	object->node = node;
	return object;
}

/* ************* Geometry ******************/

t_ecgeometry *ec_geometry_new( void)
{
	t_ecgeometry *geometry = (t_ecgeometry *) malloc( sizeof( t_ecgeometry));
	geometry->vertices = stash_new( sizeof(double) * 3 );
	geometry->faces = stash_new( sizeof(int) * 4 );
	return geometry;
}

t_ecgeometry *ec_geometry_add( t_session *session, const char *name)
{
	t_ecnode *node = ec_node_add( session, V_NT_GEOMETRY, name);
	t_ecgeometry *geometry = ec_geometry_new();
	node->data = geometry;
	geometry->node = node;
	return geometry;
}

/* ************* Checking  ******************/

int checking_count = 0;

void ec_checking_store( uint command)
{
	checking_count++;
}

void ec_checking_check( uint command)
{
}

/* ************* Node ******************/

void ec_node_print(t_ecnode *node)
{
	printf("[echo] Node %d %s\n", node->id, node->name);
}

t_ecnode *ec_node_new( int type, const char *name)
{
	t_ecnode *node = calloc( 1, sizeof( t_ecnode));
	node->ec_id = 0;
	node->type = type;
	node->ask_id = 0;
	node->has_id = 0;
	strncpy( node->name, name, NAME_SIZE);
	return node;
}

void ec_node_destroy( t_ecnode *node)
{
	verse_send_node_destroy( node->id);
}

/* ************* Links	 ******************/

void ec_session_link_pop( t_session *session, int id)
{
	t_link *l;
	t_ecnode *node = NULL;
	for( l = session->pending_links->first; l; l = l->next)
	{
		node = ( t_ecnode *) l->data;
		if( node->id == id)
		{
			lst_link_remove( session->pending_links, l);
			break;
		}
	}
}

void ec_link_push( t_session *session, t_ecnode *node)
{
	if( node->type == V_NT_OBJECT)
	{
		t_ecobject *object = ( t_ecobject *) node->data;
		if( object->node->has_id && object->target->has_id)
		{
			#ifdef DEBUG
			printf("[echo] ec_link_push, set link %s(%d) -> %s(%d)\n",
					object->node->name,
					object->node->id,
					object->target->name,
					object->target->id
					);
			#endif
			verse_send_o_link_set( object->node->id, 0, object->target->id, "geometry", 1);
			ec_session_link_pop( session, node->id);
		}
	}
	else
	{
		printf("[echo] Warning can't link node, type not implemented\n");
	}
}

/* ************* Callbacks ******************/

void ec_geometry_push( t_ecgeometry *geometry)
{
	int i;
	#ifdef DEBUG
	printf("[echo] ec_geometry_push id:%d\n", geometry->node->id);
	#endif
	for( i = 0; i < geometry->vertices->next; i++)
	{
		double *v = stash_get_elem( geometry->vertices, i);
		#ifdef DEBUG_GEOMETRY
		printf("[echo] %f %f %f\n", v[0], v[1], v[2]);
		#endif
		verse_send_g_vertex_set_xyz_real32( geometry->node->id, 0 , i, v[0], v[1], v[2]);
		if( USE_CHECKING) { }
	}

	for( i = 0; i < geometry->faces->next; i++)
	{
		int *f = stash_get_elem( geometry->faces, i);
		verse_send_g_polygon_set_corner_uint32( geometry->node->id, 1, i, f[0], f[1], f[2], f[3]);
	}
}

void ec_object_push( t_ecobject *object)
{
	#ifdef DEBUG
	printf("[echo] ec_object_push id:%d\n", object->node->id);
	#endif
}

void ec_session_node_pop( t_session *session, int id);

static void callback_node_create(void *user, VNodeID node_id, VNodeType type, VNodeOwner ownership)
{
	if( ownership == VN_OWNER_MINE)
	{

	t_ecnode *node = PENDING_NODE;

	#ifdef DEBUG
	printf("[echo] {callback: node create} ec_id:%d\n", node->ec_id);
	#endif

	/* set id */
	node->id = node_id;
	node->has_id = 1;

	/* set name */
	verse_send_node_name_set( node->id, node->name);

	/* push data */
	switch( node->type)
	{
		case V_NT_GEOMETRY: ec_geometry_push( (t_ecgeometry *) node->data); break;
		case V_NT_OBJECT: ec_object_push( (t_ecobject *) node->data); break;
		default: break;
	}

	/* pop */
	ec_session_node_pop( SESSION, node->ec_id);

	/* remove pending node */
	PENDING_NODE = NULL;
	}
}

static void enough_callback(uint connection, uint id, VNodeType type, void *user)
{
	callback_node_create( user, id, type, VN_OWNER_MINE);
}

/* ************* Session ******************/

void ec_session_node_pop( t_session *session, int id)
{
	t_link *l;
	t_ecnode *node = NULL;

	for( l = session->pending_nodes->first; l; l = l->next)
	{
		node = ( t_ecnode *) l->data;
		if( node->ec_id == id)
		{

			#ifdef DEBUG
			printf("[echo] ec_session_node_pop: id: %d {poped}\n", id);
			#endif
			lst_link_remove( session->pending_nodes, l);
			break;
		}
	}

	if( node)
	{
		switch( node->type)
		{
			case V_NT_GEOMETRY: lst_add( session->geometries, node, "."); break;
			case V_NT_OBJECT: lst_add( session->objects, node, "."); break;
			default: break;
		}
	}
}

void ec_node_push( t_session *session, t_ecnode *node)
{
	if( !PENDING_NODE)
	{
		#ifdef DEBUG
		printf("[echo] ec_node_push {create}:\n");
		ec_node_show( node);
		#endif
		PENDING_NODE = node;
		verse_send_node_create(0, node->type, VN_OWNER_MINE);
	}
}

t_ecnode *ec_node_add( t_session *session, int type, const char *name)
{
	t_ecnode *node = ec_node_new( type, name);
	lst_add( session->pending_nodes, node, ".");
	NODE_COUNT++;
	return node;
}

void ec_node_set_ready( t_ecnode *node)
{
	node->state = RENODE_READY;
}

t_session *ec_session_new( void)
{
	t_session *session = ( t_session *) calloc( 1, sizeof( t_session));
	session->pending_nodes = lst_new(".");
	session->pending_links = lst_new(".");
	session->geometries = lst_new(".");
	session->objects = lst_new(".");
	session->is_connected = 0;
	session->has_avatar = 0;
	return session;
}

void ec_session_push( t_session *session)
{
	t_link *l;
	t_ecnode *node;

	for( l = session->pending_nodes->first; l; l = l->next)
	{
		#ifdef DEBUG
		ec_pending_show();
		#endif
		node = ( t_ecnode *) l->data;
		if( node->state == RENODE_READY) ec_node_push( session, node);
		break;
	}

	for( l = session->pending_links->first; l; l = l->next)
	{
		node = ( t_ecnode *) l->data;
		if( node->state == RENODE_READY) ec_link_push( session, node);
		break;
	}
}

int ec_session_unhook( t_session *session)
{
	if( !session->pending_nodes->first) return 1;
	else return 0;
}

void ec_session_unhook_set( t_session *session)
{
	session->unhook = 1;
}

void ec_session_disconnect( t_session *session, char *msg)
{
	verse_send_connect_terminate( session->hostname, msg);
}

void ec_session_set_avatar_name( t_session *session)
{
	if( !session->has_avatar)
	{
		ENodeHead *head = e_ns_get_node_avatar( 0);
		if(head)
		{
			session->has_avatar = 1;
			verse_send_node_name_set( head->node_id, session->name);
		}
	}
}

void ec_session_update( t_session *session)
{
	if( session->is_connected)
	{
		if( DO_DISCONNECT)
		{
			ec_session_disconnect( session, DISCONNECT_MSG);
		}

		if( LOCK_GET && LOCK_USE)
		{
			LOCK_SESSION = 1;
			if( LOCK_RELEASE)
			{
				LOCK_GET = 0;
			}
		}
		else if( LOCK_ASK && !LOCK_SESSION && LOCK_USE)
		{
			LOCK_GET = 1;
			LOCK_ASK = 0;
		}
		else
		{
			/* echo update */
			ec_session_set_avatar_name(session);
			ec_session_push( session);
			/* verse update */
			e_vc_connection_update( vconnection, 1000);
			LOCK_SESSION = 0;
		}
	}
	else
	{
		if(e_vc_check_connected() && e_vc_check_accepted_slot(0))
		{
			session->is_connected = 1;
		}
		/* verse update */
		e_vc_connection_update( vconnection, 1000);
	}

}

void ec_session_connect( t_session *session, char *name, char *hostname)
{
	printf("[echo] Connecting to %s\n", hostname);

	strncpy( session->hostname, hostname, NAME_SIZE);
	strncpy( session->name, name, NAME_SIZE);

	enough_init();
	vconnection = e_vc_connect( hostname, name, "<secret>", NULL);
	e_ns_set_node_create_func( enough_callback, NULL);

	/* links node and meshnode */
	e_ns_set_custom_func(0, V_NT_GEOMETRY, ec_node_geometry);
}

/* ************* Api  ******************/

t_ecobject *ec_object_get( int id)
{
	t_link *l;
	t_lst *lst = OBJECTS;
	for( l = lst->first;l;l=l->next)
	{
		t_ecobject *object = ( t_ecobject *) l->data;
		if( object->node->ec_id == id) return object;

	}

	return NULL;
}

t_ecgeometry *ec_geometry_get( int id)
{
	t_link *l;
	t_lst *lst = GEOMETRIES;
	for( l = lst->first;l;l=l->next)
	{
		t_ecgeometry *geometry = ( t_ecgeometry *) l->data;
		if( geometry->node->ec_id == id) return geometry;

	}

	return NULL;
}

/**** Ids  ****/

int ec_api_object_get_id( int _id)
{
	int id = -1;
	t_ecobject *obj = ec_object_get( _id);
	if( obj)
	{
		t_ecnode *node = obj->node;
		if( node->has_id) id = node->id;
	}

	return id;
}

int ec_api_mesh_get_id( int _id)
{
	int id = -1;
	t_ecgeometry *geo = ec_geometry_get( _id);
	if( geo)
	{
		t_ecnode *node = ( t_ecnode *) geo->node;
		if( node->has_id) id = node->id;
	}

	return id;
}

int ec_api_object_get_echo_id( int verse_id)
{
	t_link *l;
	t_lst *lst = OBJECTS;
	for( l = lst->first;l;l=l->next)
	{
		t_ecobject *object = ( t_ecobject *) l->data;
		t_ecnode *node = object->node;
		if( node->has_id && node->id == verse_id) return node->ec_id;

	}
	return -1;
}

/**** Tags ****/

char *ec_api_tag_group_name_get( uint id_node, uint16 group_id)
{
	ENode *node = e_ns_get_node( vconnection, id_node);
	return e_ns_get_tag_group( node, group_id);
}

uint16 ec_api_tag_group_get( uint id_node, uint16 id_group)
{
	ENode *node = e_ns_get_node( vconnection, id_node);
	return e_ns_get_next_tag_group(node, id_group);
}

uint ec_api_tag_get_next( uint id_node, uint16 id_group, uint16 id_tag)
{
	ENode *node = e_ns_get_node( vconnection, id_node);
	return e_ns_get_next_tag(node, id_group, id_tag);
}

char *ec_api_tag_get_name( uint id_node, uint16 id_group, uint16 id_tag)
{
	ENodeHead *node = e_ns_get_node( vconnection, id_node);

	if( node->tag_groups)
	{
		return e_ns_get_tag_name(node, id_group, id_tag);
	}
	else
	{
		return NULL;
	}
}

VNTag *ec_api_tag_get( uint id_node, uint16 id_group, uint16 id_tag)
{
	ENode *node = e_ns_get_node( vconnection, id_node);
	return e_ns_get_tag(node, id_group, id_tag);
}

/* use id_group = 0 to create a new group, id_group = existing id ot a rename */
uint ec_api_tag_group_create( uint id_node, uint16 id_group, const char *name)
{
	uint j = -1;
	ENode *node = e_ns_get_node( vconnection, id_node);
	if( node)
	{
		uint i;
		j = 0;

		for(i = e_ns_get_next_tag_group(node, 0); i != (uint16) ~0u ; i = e_ns_get_next_tag_group(node, i + 1))
			j++;

		verse_send_tag_group_create( id_node, id_group, name);

	}
	else
	{
		printf("[echo_minuit] group_create: can't find node %d\n", id_node);
	}

	return j;
}

uint ec_api_tag_create( VNodeID id_node, uint16 id_group, uint16 id_tag, const char *name, VNTagType type, VNTag *tag)
{
	switch( type)
	{
		case VN_TAG_UINT32:
			{
			uint k = 0;
				uint j = 0;
				uint i = id_group;
				ENode *node = e_ns_get_node( vconnection, id_node);

				for(j = e_ns_get_next_tag(node, i, 0); j != (uint16) ~0u ; j = e_ns_get_next_tag(node, i, j + 1))
					k++;

				verse_send_tag_create( id_node, id_group, id_tag, name, type, tag);

				return k;
			break;
			}

		default:
			printf("[echo] TagType not supported\n");
			return -1;
	}
}

uint ec_api_tag_create_int( VNodeID id_node, uint16 id_group, uint16 id_tag, const char *name, VNTagType type, uint val)
{
	VNTag tag;
	tag.vuint32 = val;
	return ec_api_tag_create( id_node, id_group, id_tag, name, type, &tag);
}

/**** Meshes ****/

void ec_geometry_add_face( t_ecgeometry *geometry, int a, int b, int c, int d)
{
	int data[] = {a,b,c,d};
	stash_add( geometry->faces, data);
}

void ec_geometry_add_vertex( t_ecgeometry *geometry, double x, double y, double z)
{
	double data[] = {x,y,z};
	stash_add( geometry->vertices, data);
}

void ec_api_mesh_face_add( int id, int a, int b, int c, int d)
{
	t_ecgeometry *geometry = ec_geometry_get( id);
	if( geometry) ec_geometry_add_face( geometry, a, b, c, d);
}

void ec_api_mesh_vertex_add( int id, double x, double y, double z)
{
	t_ecgeometry *geometry = ec_geometry_get( id);
	if( geometry) ec_geometry_add_vertex( geometry, x, y, z);
}

void ec_api_mesh_push( int id)
{
	t_ecgeometry *geometry = ec_geometry_get( id);
	if ( geometry) ec_node_set_ready( geometry->node);
	else printf("[echo] Error can't push geometry %d\n", id);
}

int ec_api_mesh_add( char *name)
{
	if (!SESSION) return -1;

	t_ecgeometry *geometry = ec_geometry_add( SESSION, name);
	geometry->node->ec_id = GEOMETRY_COUNT;
	lst_add( GEOMETRIES, geometry, "geometry");

	#ifdef DEBUG
	printf("[echo] ec_api_mesh_add: %s ", name);
	ec_node_show( geometry->node);
	#endif

	GEOMETRY_COUNT++;

	return GEOMETRY_COUNT - 1;
}

/**** Objects ****/

void ec_api_object_link_push( int id_object, int id_geometry)
{
	t_ecobject *object = ec_object_get( id_object);
	t_ecgeometry *geometry = ec_geometry_get( id_geometry);
	if( object && geometry)
	{
		object->target = geometry->node;
		lst_add( SESSION->pending_links, object->node, ".");
	}
}

void ec_api_object_push( int id)
{
	t_ecobject *object = ec_object_get( id);
	if( object) ec_node_set_ready( object->node);
	else printf("[echo] Error can't push object %d\n", id);
}

int ec_api_object_add( char *name)
{
	if (!SESSION) return -1;

	t_ecobject *object = ec_object_add( SESSION, name);
	object->node->ec_id = OBJECT_COUNT;
	lst_add( OBJECTS, object, "object");

	#ifdef DEBUG
	printf("[echo] ec_api_object_add: %s ", name);
	ec_node_show( object->node);
	#endif

	OBJECT_COUNT++;

	return OBJECT_COUNT - 1;
}

/**** Session ****/

int ec_api_check_connect( void)
{
	if(SESSION)
		if(SESSION->is_connected)
		       	return 1;
	return 0;
}

int ec_api_lock_use( void)
{
	return LOCK_USE;
}

void ec_api_lock_ask( void)
{
	LOCK_ASK = 1;
}

int ec_api_lock_get( void)
{
	return LOCK_GET;
}

void ec_api_lock_release( void)
{
	LOCK_RELEASE = 1;
}

int ec_api_unhook( void)
{
	if( SESSION) return ec_session_unhook( SESSION);
	else return 1;
}

void ec_api_disconnect( char *msg)
{
	strncpy(DISCONNECT_MSG,msg,DISCONNECT_MSG_LENGTH);
	DO_DISCONNECT = 1;
}

 void ec_api_connect( char *name, char *hostname)
{
	if( SESSION) ec_session_connect( SESSION, name, hostname);
}

void ec_api_update( void)
{
	if( SESSION) ec_session_update( SESSION);
}

void ec_api_init( void)
{
	SESSION = ec_session_new();
	OBJECTS = lst_new("objects");
	GEOMETRIES = lst_new("geoemetries");
}


/* vim: set noet sts=8 sw=8: */
