all: libecho
libecho:echo 
	cd echo && $(MAKE)

clean:
	cd echo && make clean


