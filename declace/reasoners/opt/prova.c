#include <stdio.h>

int transfer_time(float size, float bw, float latency) {
    return (int) (size * 8000.0 / bw + latency);
}

// cc -fPIC -shared -o my_functions.so my_functions.c