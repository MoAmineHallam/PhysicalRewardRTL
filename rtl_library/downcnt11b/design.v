// 11-bit down-counter.
module downcnt11b (
    input  wire clk, rst_n,
    output reg  [10:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {11{1'b1}};
        else        count <= count - 11'd1;
    end
endmodule
