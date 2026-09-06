module correctness_s2__poly8_v9_8b__g1 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= ((((((((16'd65 * x + 16'd30) * x + 16'd3) * x + 16'd97) * x + 16'd7) * x + 16'd99) * x + 16'd95) * x + 16'd42) * x + 16'd1) & 16'hFFFF;
    end
endmodule
