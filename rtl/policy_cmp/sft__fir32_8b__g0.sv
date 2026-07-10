module sft__fir32_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] mem0[0:31];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 32; i = i + 1) mem0[i] <= 8'd0;
            y <= 16'd0;
        end else begin
            mem0[0] <= x;
            for (i = 1; i < 32; i = i + 1) mem0[i] <= mem0[i-1];
            y <= mem0[0] * 8'd3 + mem0[1] * 8'd5 + mem0[2] * 8'd7 + mem0[3] * 8'd9 + mem0[4] * 8'd11 + mem0[5] * 8'd13 + mem0[6] * 8'd15 + mem0[7] * 8'd17 + mem0[8] * 8'd19 + mem0[9] * 8'd21 + mem0[10] * 8'd23 + mem0[11] * 8'd25 + mem0[12] * 8'd27 + mem0[13] * 8'd29 + mem0[14] * 8'd31 + mem0[15] * 8'd33 + mem0[16] * 8'd33 + mem0[17] * 8'd31 + mem0[18] * 8'd29 + mem0[19] * 8'd27 + mem0[20] * 8'd25 + mem0[21] * 8'd23 + mem0[22] * 8'd21 + mem0[23] * 8'd19 + mem0[24] * 8'd17 + mem0[25] * 8'd15 + mem0[26] * 8'd13 + mem0[27] * 8'd11 + mem0[28] * 8'd9 + mem0[29] * 8'd7 + mem0[30] * 8'd5 + mem0[31] * 8'd3;
        end
    end
endmodule