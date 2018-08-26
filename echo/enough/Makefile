CC=gcc
CFLAGS=-std=gnu99 -I../verse/ -L../verse/ -L./ -fPIC -g -DDEBUG
LDFLAGS=-lm -g 

SRC = e_storage_audio.c e_storage_bitmap.c e_storage_curve.c e_storage_geometry.c e_storage_head.c e_storage_material.c \
		e_storage_node.c e_storage_object.c e_storage_text.c st_types.c

OBJ = $(SRC:%.c=%.o)

enough.a: $(OBJ)
	ar -rcs libenough.a  $(OBJ)

clean:
	rm *.o
	rm libenough.a

