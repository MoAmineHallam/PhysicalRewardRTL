module sft__poly7_v5_8b__g4 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    always @(posedge clk) begin
        if (!rst_n) y <= 16'd0;
        else        y <= (((((((16'd53 * x + 16'd68) * x + 16'd36) * x + 16'd67) * x + 16'd8) * x + 16'd1) * x + 16'd93) * x + 16'd82) & 16'hFFFF;
    end
endmodule