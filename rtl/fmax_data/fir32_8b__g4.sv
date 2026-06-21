module fir32_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] samples [0:31];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) samples[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            samples[0] <= x;
            for (i = 1; i < 32; i = i + 1) samples[i] <= samples[i-1];
            y <= samples[0] * 8'd3 + samples[1] * 8'd5 + samples[2] * 8'd7 + samples[3] * 8'd9 + samples[4] * 8'd11 + samples[5] * 8'd13 + samples[6] * 8'd15 + samples[7] * 8'd17 + samples[8] * 8'd19 + samples[9] * 8'd21 + samples[10] * 8'd23 + samples[11] * 8'd25 + samples[12] * 8'd27 + samples[13] * 8'd29 + samples[14] * 8'd31 + samples[15] * 8'd33 + samples[16] * 8'd33 + samples[17] * 8'd31 + samples[18] * 8'd29 + samples[19] * 8'd27 + samples[20] * 8'd25 + samples[21] * 8'd23 + samples[22] * 8'd21 + samples[23] * 8'd19 + samples[24] * 8'd17 + samples[25] * 8'd15 + samples[26] * 8'd13 + samples[27] * 8'd11 + samples[28] * 8'd9 + samples[29] * 8'd7 + samples[30] * 8'd5 + samples[31] * 8'd3;
        end
    end
endmodule