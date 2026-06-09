// Registered 4-to-8 bit sign extension.
module sign_ext (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] in4,
    output reg  [7:0] out8
);
    always @(posedge clk) begin
        if (!rst_n) out8 <= 8'b0;
        else        out8 <= {{4{in4[3]}}, in4};
    end
endmodule
