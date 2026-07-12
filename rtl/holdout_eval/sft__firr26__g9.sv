module sft__firr26__g9 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17, d18, d19, d20, d21, d22, d23, d24, d25;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; d2 <= 8'd0; d3 <= 8'd0; d4 <= 8'd0; d5 <= 8'd0; d6 <= 8'd0; d7 <= 8'd0; d8 <= 8'd0; d9 <= 8'd0; d10 <= 8'd0; d11 <= 8'd0; d12 <= 8'd0; d13 <= 8'd0; d14 <= 8'd0; d15 <= 8'd0; d16 <= 8'd0; d17 <= 8'd0; d18 <= 8'd0; d19 <= 8'd0; d20 <= 8'd0; d21 <= 8'd0; d22 <= 8'd0; d23 <= 8'd0; d24 <= 8'd0; d25 <= 8'd0; y <= 16'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
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
            d19 <= d18;
            d20 <= d19;
            d21 <= d20;
            d22 <= d21;
            d23 <= d22;
            d24 <= d23;
            d25 <= d24;
            y <= 16'd1 * d0 + 16'd2 * d1 + 16'd3 * d2 + 16'd4 * d3 + 16'd5 * d4 + 16'd6 * d5 + 16'd7 * d6 + 16'd8 * d7 + 16'd9 * d8 + 16'd10 * d9 + 16'd11 * d10 + 16'd12 * d11 + 16'd13 * d12 + 16'd14 * d13 + 16'd15 * d14 + 16'd16 * d15 + 16'd17 * d16 + 16'd18 * d17 + 16'd19 * d18 + 16'd20 * d19 + 16'd21 * d20 + 16'd22 * d21 + 16'd23 * d22 + 16'd24 * d23 + 16'd25 * d24 + 16'd26 * d25;
        end
    end
endmodule