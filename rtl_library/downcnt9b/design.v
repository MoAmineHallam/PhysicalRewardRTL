// 9-bit down-counter.
module downcnt9b (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {9{1'b1}};
        else        count <= count - 9'd1;
    end
endmodule
