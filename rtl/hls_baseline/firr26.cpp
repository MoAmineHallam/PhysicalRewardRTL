// firr26: 26-tap FIR, y = (sum H[k]*x[n-k]) mod 2^16 (oracle-exact).
#include <stdint.h>

void firr26(uint8_t x, uint16_t *y) {
#pragma HLS INTERFACE ap_ctrl_none port=return
#ifndef NO_PRAGMA
#pragma HLS pipeline II=1
#endif
    static uint8_t line[26] = {0};
#ifndef NO_PRAGMA
#pragma HLS array_partition variable=line complete
#endif
    static const uint16_t H[26] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26};
    for (int k = 25; k > 0; k--) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        line[k] = line[k - 1];
    }
    line[0] = x;
    uint32_t acc = 0;
    for (int k = 0; k < 26; k++) {
#ifndef NO_PRAGMA
#pragma HLS unroll
#endif
        acc += (uint32_t)H[k] * line[k];
    }
    *y = (uint16_t)acc;
}
