// 8-bit down-counter.
module downcnt8b (
    input  wire clk, rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {8{1'b1}};
        else        count <= count - 8'd1;
    end
endmodule
