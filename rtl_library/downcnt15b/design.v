// 15-bit down-counter.
module downcnt15b (
    input  wire clk, rst_n,
    output reg  [14:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {15{1'b1}};
        else        count <= count - 15'd1;
    end
endmodule
