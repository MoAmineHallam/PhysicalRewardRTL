// 2-to-4 one-hot decoder (registered).
module decoder2to4 (
    input  wire clk, rst_n,
    input  wire [1:0] sel,
    output reg  [3:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (4'd1 << sel);
    end
endmodule
