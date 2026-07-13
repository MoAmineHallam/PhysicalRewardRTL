// self-checking TB for firr18 (g++ pre-flight AND Vitis HLS csim).
#include <stdio.h>
#include <stdint.h>
#include "firr18_golden.h"

void firr18(uint8_t x, uint16_t *y);

int main() {
    int bad = 0;
    for (int i = 0; i < GOLDEN_N; i++) {
        uint16_t y;
        firr18(STIM[i], &y);
        if (y != GOLDEN[i]) {
            if (bad < 5)
                printf("MISMATCH @%d: x=%u got=%u want=%u\n",
                       i, (unsigned)STIM[i], (unsigned)y, (unsigned)GOLDEN[i]);
            bad++;
        }
    }
    printf("%s: %s (%d/%d)\n", "firr18", bad ? "FAIL" : "PASS",
           GOLDEN_N - bad, GOLDEN_N);
    return bad ? 1 : 0;
}
