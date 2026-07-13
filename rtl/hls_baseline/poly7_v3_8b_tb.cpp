// self-checking TB for poly7_v3_8b (g++ pre-flight AND Vitis HLS csim).
#include <stdio.h>
#include <stdint.h>
#include "poly7_v3_8b_golden.h"

void poly7_v3_8b(uint8_t x, uint16_t *y);

int main() {
    int bad = 0;
    for (int i = 0; i < GOLDEN_N; i++) {
        uint16_t y;
        poly7_v3_8b(STIM[i], &y);
        if (y != GOLDEN[i]) {
            if (bad < 5)
                printf("MISMATCH @%d: x=%u got=%u want=%u\n",
                       i, (unsigned)STIM[i], (unsigned)y, (unsigned)GOLDEN[i]);
            bad++;
        }
    }
    printf("%s: %s (%d/%d)\n", "poly7_v3_8b", bad ? "FAIL" : "PASS",
           GOLDEN_N - bad, GOLDEN_N);
    return bad ? 1 : 0;
}
