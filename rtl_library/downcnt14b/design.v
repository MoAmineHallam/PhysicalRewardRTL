// 14-bit down-counter.
module downcnt14b (
    input  wire clk, rst_n,
    output reg  [13:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {14{1'b1}};
        else        count <= count - 14'd1;
    end
endmodule
