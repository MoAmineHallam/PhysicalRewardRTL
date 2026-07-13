// fir10_8b: 10-tap FIR, y = (sum H[k]*x[n-k]) mod 2^16 (oracle-exact).
#include <stdint.h>

void fir10_8b(uint8_t x, uint16_t *y) {
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static uint8_t line[10] = {0};
#ifndef NO_PRAGMA
#pragma HLS array_partition variable=line complete
#endif
    static const uint16_t H[10] = {3, 5, 7, 9, 11, 11, 9, 7, 5, 3};
    for (int k = 9; k > 0; k--) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        line[k] = line[k - 1];
    }
    line[0] = x;
    uint32_t acc = 0;
    for (int k = 0; k < 10; k++) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc += (uint32_t)H[k] * line[k];
    }
    *y = (uint16_t)acc;
}
