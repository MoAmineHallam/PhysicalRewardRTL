module sft__poly12_v15_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((((((((16'd48 * x + 16'd24) * x + 16'd79) * x + 16'd2) * x + 16'd46) * x + 16'd35) * x + 16'd44) * x + 16'd66) * x + 16'd80) * x + 16'd64) * x + 16'd18) * x + 16'd58) * x + 16'd51)) & 16'hFFFF;
    end
endmodule
