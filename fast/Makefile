# Grab the targets from the src directory.
TARGETS = $(patsubst src/%.cxx, bin/%, $(wildcard src/*.cxx))
COREOBJ = $(patsubst core/src/%.cxx, core/build/%.o, $(wildcard core/src/*.cxx))
#DEPSOBJ = $(patsubst core/src/drs/%.c, core/build/%.o, $(wildcard core/src/drs/*.c))
#DEPSOBJ += $(patsubst core/src/drs/%.cpp, core/build/%.o, $(wildcard core/src/drs/*.cpp))
DEPSOBJ += $(patsubst core/include/vme/%.c, core/build/%.o, $(wildcard core/include/vme/*.c))

# Figure out the architecture
UNAME_S = $(shell uname -s)

# Clang compiler
ifeq ($(UNAME_S), Darwin)
	CXX = clang++
	CC  = clang
	FLAGS = -std=c++11 -DOS_DARWIN
endif

# Gnu compiler
ifeq ($(UNAME_S), Linux)
	CXX = g++
	CC  = gcc
	FLAGS = -std=c++0x -DOS_LINUX
endif

ifdef DEBUG
	FLAGS += -g -pthread
else
	FLAGS += -g -pthread
endif

# ROOT libs and flags
FLAGS += $(shell root-config --cflags)
LIBS = $(shell root-config --libs)

FLAGS += -Icore/include -Icore/include/drs -Icore/json11
LIBS += -lm -lzmq -lCAENDigitizer -lusb-1.0 -lutil -lpthread

COREOBJ += core/build/json11.o

all: $(COREOBJ) $(DEPSOBJ) $(TARGETS)

bin/fe_%: src/fe_%.cxx $(COREOBJ) $(DEPSOBJ)
	$(CXX) -o $@ $+ $(FLAGS) $(LIBS)

bin/%_daq: modules/%_daq.cxx 
	$(CXX) -o $@ $+ $(FLAGS) $(LIBS)

bin/%: src/%.cxx $(COREOBJ) $(DEPSOBJ)
	$(CXX) -o $@ $+ $(FLAGS) $(LIBS)

core/build/%.o: core/src/%.cxx
	cd core; make; cd ..

clean:
	cd core && make clean && cd ..; \
	rm -f $(TARGETS) $(COREOBJ) $(DEPSOBJ)
