// poly8_v7_8b: degree-8 Horner polynomial mod 2^16 (oracle-exact).
#include <stdint.h>

void poly8_v7_8b(uint8_t x, uint16_t *y) {
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static const uint16_t C[9] = {57, 11, 20, 96, 53, 74, 25, 52, 15};
    uint16_t acc = C[0];
    for (int k = 1; k <= 8; k++) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc = (uint16_t)(acc * x + C[k]);
    }
    *y = acc;
}
