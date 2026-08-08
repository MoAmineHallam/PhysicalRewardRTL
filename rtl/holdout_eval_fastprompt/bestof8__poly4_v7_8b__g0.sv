module bestof8__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((16'd24 * x + 16'd36) * x + 16'd17) * x + 16'd21) * x + 16'd50)) & 16'hFFFF;
    end
endmodule