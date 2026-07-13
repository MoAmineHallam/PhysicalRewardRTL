// poly4_v6_8b: degree-4 Horner polynomial mod 2^16 (oracle-exact).
#include <stdint.h>

void poly4_v6_8b(uint8_t x, uint16_t *y) {
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static const uint16_t C[5] = {65, 29, 88, 44, 17};
    uint16_t acc = C[0];
    for (int k = 1; k <= 4; k++) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc = (uint16_t)(acc * x + C[k]);
    }
    *y = acc;
}
