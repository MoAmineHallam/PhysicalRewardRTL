module sft__firr18__g8 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18;
    wire [23:0] acc = 8'd1 * d1 + 8'd2 * d2 + 8'd3 * d3 + 8'd4 * d4 + 8'd5 * d5 + 8'd6 * d6 + 8'd7 * d7 + 8'd8 * d8 + 8'd9 * d9 + 8'd10 * d10 + 8'd11 * d11 + 8'd12 * d12 + 8'd13 * d13 + 8'd14 * d14 + 8'd15 * d15 + 8'd16 * d16 + 8'd17 * d17 + 8'd18 * d18;
    always @(posedge clk) begin
        if (!rst_n) begin
            d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0; d10 <= 8'd0; d11 <= 8'd0; d12 <= 8'd0; d13 <= 8'd0; d14 <= 8'd0; d15 <= 8'd0; d16 <= 8'd0; d17 <= 8'd0; d18 <= 8'd0; y <= 16'd0;
        end else begin
            d1 <= x;
            d2 <= d1;
            d3 <= d2;
            d4 <= d3;
            d5 <= d4;
            d6 <= d5;
            d7 <= d6;
            d8 <= d7;
            d9 <= d8;
            d10 <= d9;
            d11 <= d10;
            d12 <= d11;
            d13 <= d12;
            d14 <= d13;
            d15 <= d14;
            d16 <= d15;
            d17 <= d16;
            d18 <= d17;
            y <= acc[15:0];
        end
    end
endmodule