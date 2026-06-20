module poly6_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((16'd1 * x + 16'd3) * x + 16'd5) * x + 16'd7) * x + 16'd9) * x + 16'd11) * x + 16'd13)) & 16'hFFFF;
    end
endmodule