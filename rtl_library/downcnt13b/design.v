// 13-bit down-counter.
module downcnt13b (
    input  wire clk, rst_n,
    output reg  [12:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {13{1'b1}};
        else        count <= count - 13'd1;
    end
endmodule
