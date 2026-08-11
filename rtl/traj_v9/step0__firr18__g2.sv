module step0__firr18__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  d0, d1, d2, d3, d4, d5, d6, d7, d8, d9, d10, d11, d12, d13, d14, d15, d16, d17;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'b0; d1 <= 8'b0; d2 <= 8'b0; d3 <= 8'b0; d4 <= 8'b0; d5 <= 8'b0; d6 <= 8'b0; d7 <= 8'b0; d8 <= 8'b0; d9 <= 8'b0; d10 <= 8'b0; d11 <= 8'b0; d12 <= 8'b0; d13 <= 8'b0; d14 <= 8'b0; d15 <= 8'b0; d16 <= 8'b0; d17 <= 8'b0; y <= 16'b0;
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
            y <= d0*(1'd1) + d1*(2'd2) + d2*(3'd3) + d3*(4'd4) + d4*(5'd5) + d5*(6'd6) + d6*(7'd7) + d7*(8'd8) + d8*(9'd9) + d9*(10'd10) + d10*(11'd11) + d11*(12'd12) + d12*(13'd13) + d13*(14'd14) + d14*(15'd15) + d15*(16'd16) + d16*(17'd17) + d17*(18'd18);
        end
    end
endmodule