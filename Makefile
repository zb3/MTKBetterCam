CC=gcc

PROG = fixraw
all: $(PROG)

fixraw: fixraw.c
	$(CC) -o fixraw fixraw.c 


.PHONY: clean

clean:
	rm -f $(PROG)