// 12-bit down-counter.
module downcnt12b (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {12{1'b1}};
        else        count <= count - 12'd1;
    end
endmodule
