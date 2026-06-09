// 10-bit down-counter.
module downcnt10b (
    input  wire clk, rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {10{1'b1}};
        else        count <= count - 10'd1;
    end
endmodule
