// 6-bit down-counter.
module downcnt6b (
    input  wire clk, rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {6{1'b1}};
        else        count <= count - 6'd1;
    end
endmodule
