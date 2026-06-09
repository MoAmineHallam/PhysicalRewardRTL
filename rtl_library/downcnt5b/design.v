// 5-bit down-counter.
module downcnt5b (
    input  wire clk, rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {5{1'b1}};
        else        count <= count - 5'd1;
    end
endmodule
