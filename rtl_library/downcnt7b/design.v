// 7-bit down-counter.
module downcnt7b (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {7{1'b1}};
        else        count <= count - 7'd1;
    end
endmodule
