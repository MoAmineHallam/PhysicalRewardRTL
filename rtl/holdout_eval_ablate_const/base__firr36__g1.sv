module base__firr36__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [7:0] tap [0:35];    // 36-tap delay line
    integer k;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            y <= 0;
            for (k = 0; k < 36; k = k + 1) begin
                tap[k] <= 0;
            end
        end
        else begin
            // shift the tap line down by one
            for (k = 35; k > 0; k = k - 1) begin
                tap[k] <= tap[k-1];
            end
            // add the new sample to the start of the tap line
            tap[0] <= x;
            // compute the new output value
            y <= (tap[0]+tap[1]*2+tap[2]*3+tap[3]*4+tap[4]*5+tap[5]*6+tap[6]*7+tap[7]*8+tap[8]*9+tap[9]*10+tap[10]*11+tap[11]*12+tap[12]*13+tap[13]*14+tap[14]*15+tap[15]*16+tap[16]*17+tap[17]*18+tap[18]*19+tap[19]*20+tap[20]*21+tap[21]*22+tap[22]*23+tap[23]*24+tap[24]*25+tap[25]*26+tap[26]*27+tap[27]*28+tap[28]*29+tap[29]*30+tap[30]*31+tap[31]*32+tap[32]*33+tap[33]*34+tap[34]*35+tap[35]*36);
        end
    end

endmodule