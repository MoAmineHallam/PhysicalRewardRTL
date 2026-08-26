module sft__poly6_v13_8b__g6 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= ((((((16'd86 * x + 16'd73) * x + 16'd23) * x + 16'd69) * x + 16'd48) * x + 16'd52) * x + 16'd39);
    end
endmodule
