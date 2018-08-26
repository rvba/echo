/* 
 * Copyright (C) 2018 Milovann Yanatchkov 
 *
 * This file is part of Echo , a free software
 * licensed under the GNU General Public License v2
 * see /LICENSE for more information
 *
 */

#ifndef __ECHO_H__
#define __ECHO_H__

#include "verse.h"
#include "enough.h"

#define NAME_SIZE 128

typedef uint32 VNodeID;
struct ENode;
struct Stash;

typedef struct Ec_Node
{
	char name[NAME_SIZE];
	VNodeType type;
	VNodeID id;			/** Verse ID*/
	int ec_id;			/** Echo ID*/
	int ask_id;
	int has_id;
	int state;
	void *data;

}t_ecnode;

typedef struct Ec_Object
{
	t_ecnode *node;			/** Node Reference */
	t_ecnode *target;		/** Node Geometry */

}t_ecobject;

typedef struct Ec_Geometry
{
	t_ecnode *node;			/** Node reference */
	struct Stash *vertices;		/** Vertices */
	struct Stash *faces;		/** Faces*/
	int pushed;			/**set when pushed to the server */

}t_ecgeometry;

void ec_test_enough( void);
void ec_node_geometry(ENode *node, ECustomDataCommand command);

VNodeID		ec_api_get_link_node( VNodeID node_id, uint link_id);
uint		ec_api_object_node_get_links_count( uint id);
char *		ec_api_object_node_get_link_name( uint node_id, uint link_id);
int		ec_api_object_get_echo_id( int verse_id);
int		ec_api_object_get_id( int _id); /* form echo id to verse id */
int		ec_api_mesh_get_id( int _id);

uint		ec_api_node_get_next( VNodeType type, uint id);
uint		ec_api_node_get_count( VNodeType type);
uint		ec_api_object_node_get_count( void);
uint		ec_api_object_node_get_next( uint id); /* starts at 0 */
int		ec_api_object_add( char *name);
void		ec_api_object_push( int id);
void		ec_api_object_link_push( int id_object, int id_geometry);

/* Session  */
int	ec_api_lock_use( void);
void	ec_api_lock_ask( void);
int	ec_api_lock_get( void);
void	ec_api_lock_release( void);
void	ec_api_init( void);
void	ec_api_connect( char *name, char *hostname);
void	ec_api_disconnect( char *msg);
void	ec_api_update( void);
int	ec_api_check_connect( void);

int	ec_api_mesh_add( char *name);
void	ec_api_mesh_vertex_add( int id, double x, double y, double z);
void	ec_api_mesh_vertex_set( int id, int indice, double x, double y, double z);
void	ec_api_mesh_vertex_delete( int id, int indice);
void	ec_api_mesh_push( int id);
void	ec_api_mesh_face_add( int id, int a, int b, int c, int d);
void	ec_api_mesh_face_delete( int id, int indice);

/* tags */
char *ec_api_tag_group_name_get( uint id_node, uint16 group_id);
uint ec_api_tag_group_create( uint id_node, uint16 id_group, const char *name);
uint ec_api_tag_create( VNodeID id_node, uint16 id_group, uint16 id_tag, const char *name, VNTagType type, VNTag *tag);
uint ec_api_tag_create_int( VNodeID id_node, uint16 id_group, uint16 id_tag, const char *name, VNTagType type, uint val);
//uint16 ec_api_tag_group_get( uint id_node, const char *name);

uint16 ec_api_tag_group_get( uint id_node, uint16 group_id);
uint ec_api_tag_get_next( uint id_node, uint16 id_group, uint16 tag_id);
char *ec_api_tag_get_name( uint id_node, uint16 id_group, uint16 id_tag);
VNTag *ec_api_tag_get( uint id_node, uint16 id_group, uint16 id_tag);

/* nodes */
uint ec_api_get_node_owner( uint id);
char *ec_api_get_node_name( uint id);

double *ec_api_get_object_position( uint id);
uint ec_api_get_object_visibility( uint id);

/* mesh */
t_ecgeometry *ec_api_geometry_get( int id);
uint ec_get_mesh_object( uint id_object);
uint ec_api_get_mesh_vertex_count( uint id);
uint ec_api_get_mesh_face_count( uint id);
egreal *ec_api_get_mesh_vertices( uint id);
uint *ec_api_get_mesh_faces( uint id);

uint ec_api_get_node_version_data( uint id);



#endif
