module sft__poly7_v5_8b__g2 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    wire [15:0] p0 = 16'd53;
    wire [15:0] p1 = p0 * x + 16'd68;
    wire [15:0] p2 = p1 * x + 16'd36;
    wire [15:0] p3 = p2 * x + 16'd67;
    wire [15:0] p4 = p3 * x + 16'd8;
    wire [15:0] p5 = p4 * x + 16'd1;
    wire [15:0] p6 = p5 * x + 16'd93;
    wire [15:0] p7 = p6 * x + 16'd82;
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= p7;
    end
endmodule