// 16-bit binary up-counter.
module counter16b (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 16'd0;
        else        count <= count + 16'd1;
    end
endmodule
