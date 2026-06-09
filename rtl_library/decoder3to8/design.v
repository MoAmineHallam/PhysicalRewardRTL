// 3-to-8 one-hot decoder (registered).
module decoder3to8 (
    input  wire clk, rst_n,
    input  wire [2:0] sel,
    output reg  [7:0] out
);
    always @(posedge clk) begin
        if (!rst_n) out <= 0;
        else        out <= (8'd1 << sel);
    end
endmodule
