module sft__firr10__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg  [7:0]  xs0, xs1, xs2, xs3, xs4, xs5, xs6, xs7, xs8, xs9;
    wire [23:0] acc = 8'd1 * xs0 + 8'd2 * xs1 + 8'd3 * xs2 + 8'd4 * xs3 + 8'd5 * xs4 + 8'd6 * xs5 + 8'd7 * xs6 + 8'd8 * xs7 + 8'd9 * xs8 + 8'd10 * xs9;
    always @(posedge clk) begin
        if (!rst_n) begin
            xs0 <= 8'd0; xs1 <= 8'd0; xs2 <= 8'd0; xs3 <= 8'd0; xs4 <= 8'd0; xs5 <= 8'd0; xs6 <= 8'd0; xs7 <= 8'd0; xs8 <= 8'd0; xs9 <= 8'd0; y <= 16'd0;
        end else begin
            xs0 <= x;
            xs1 <= xs0;
            xs2 <= xs1;
            xs3 <= xs2;
            xs4 <= xs3;
            xs5 <= xs4;
            xs6 <= xs5;
            xs7 <= xs6;
            xs8 <= xs7;
            xs9 <= xs8;
            y <= acc[15:0];
        end
    end
endmodule