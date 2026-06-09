// 4-bit down-counter.
module downcnt4b (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {4{1'b1}};
        else        count <= count - 4'd1;
    end
endmodule
