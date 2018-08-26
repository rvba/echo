CC=gcc
CFLAGS=-std=gnu99 -I./umber -I./verse/ -L./verse/ -I./enough/ -L./ -fPIC -g 

ifeq ($(OS),Windows_NT)
	LDFLAGS=-lm -g -lws2_32 -static-libgcc -static-libstdc++
	ifeq ($(PROCESSOR_ARCHITECTURE),AMD64)
	   v = 64
	else
	   v = 32
	endif
	MAKE=build.bat
	CLEAN=
	DL=
	EXT=dll
else
	LDFLAGS=-lm -g 
	LBITS := $(shell getconf LONG_BIT)
	ifeq ($(LBITS),64)
	   v = 64
	else
	   v = 32 
	endif
	MAKE=make
	CLEAN=make clean
	DL=-ldl
	EXT=so
endif

SRC=echo.c echo.h 
OBJ = $(SRC:%.c=%.o)

all: umber verse enough libecho 

verse: libverse.a
libverse.a: 
	cd verse && $(MAKE)

umber: libumber.a
libumber.a:
	cd umber && $(MAKE)

enough: libenough.a
libenough.a:
	cd enough && $(MAKE)

libecho: $(OBJ)
		gcc -shared $(DL) -Wl,-soname,libecho$(v).$(EXT) -o libecho$(v).$(EXT) \
			$(OBJ) enough/libenough.a verse/libverse.a umber/libumber.a $(CFLAGS) $(LDFLAGS)
		
echo: echo.o $(OBJ) 
	gcc -o _echo $^ $(CFLAGS) $(LDFLAGS)

clean:
	rm libecho$(v).$(EXT)
	rm *.o

	cd verse && $(CLEAN)
	cd umber && $(CLEAN)
	cd enough && $(CLEAN)
