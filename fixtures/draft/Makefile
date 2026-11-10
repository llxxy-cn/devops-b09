CC ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror
TARGET := app
OBJECTS := main.o helper.o

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $(OBJECTS)

main.o: main.c helper.h
	$(CC) $(CFLAGS) -c main.c

helper.o: helper.c helper.h config.h
	$(CC) $(CFLAGS) -c helper.c

test: $(TARGET)
	@test "$$(./$(TARGET))" = "hello E3"

clean:
	rm -f $(TARGET) $(OBJECTS)
