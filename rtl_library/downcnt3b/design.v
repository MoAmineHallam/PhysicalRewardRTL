// 3-bit down-counter.
module downcnt3b (
    input  wire clk, rst_n,
    output reg  [2:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {3{1'b1}};
        else        count <= count - 3'd1;
    end
endmodule
