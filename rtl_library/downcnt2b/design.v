// 2-bit down-counter.
module downcnt2b (
    input  wire clk, rst_n,
    output reg  [1:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {2{1'b1}};
        else        count <= count - 2'd1;
    end
endmodule
