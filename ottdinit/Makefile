CFLAGS = -Wall
LDFLAGS = -levent
CFLAGS = -g

all: init init_debug daemon

daemon: process.o

process.o: process.c process.h

install :
	cp init /home/myottd/dev/openttd/fs_base/root/sbin/

