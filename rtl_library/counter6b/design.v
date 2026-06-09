// 6-bit binary up-counter.
module counter6b (
    input  wire clk,
    input  wire rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 6'd0;
        else        count <= count + 6'd1;
    end
endmodule
