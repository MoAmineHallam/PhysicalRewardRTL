// 8-bit binary up-counter.
module counter8b (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 8'd0;
        else        count <= count + 8'd1;
    end
endmodule
