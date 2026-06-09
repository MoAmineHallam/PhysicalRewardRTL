// 4-to-16 one-hot decoder (registered).
module decoder4to16 (
    input  wire clk, rst_n,
    input  wire [3:0] sel,
    output reg  [15:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (16'd1 << sel);
    end
endmodule
