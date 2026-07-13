// self-checking TB for firr6 (g++ pre-flight AND Vitis HLS csim).
#include <stdio.h>
#include <stdint.h>
#include "firr6_golden.h"

void firr6(uint8_t x, uint16_t *y);

int main() {
    int bad = 0;
    for (int i = 0; i < GOLDEN_N; i++) {
        uint16_t y;
        firr6(STIM[i], &y);
        if (y != GOLDEN[i]) {
            if (bad < 5)
                printf("MISMATCH @%d: x=%u got=%u want=%u\n",
                       i, (unsigned)STIM[i], (unsigned)y, (unsigned)GOLDEN[i]);
            bad++;
        }
    }
    printf("%s: %s (%d/%d)\n", "firr6", bad ? "FAIL" : "PASS",
           GOLDEN_N - bad, GOLDEN_N);
    return bad ? 1 : 0;
}
