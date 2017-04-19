CC = gcc
#CFLAGSW2V = -lm -O0 -pthread -march=native -Wall -ggdb
CFLAGSW2V = -lm -pthread -O3 -march=native -Wall -funroll-loops -Wno-unused-result

all: paper2vec

word2vec : word2vec.c
	$(CC) paper2vec.c -o paper2vec $(CFLAGSW2V)
clean:
	rm -rf paper2vec
