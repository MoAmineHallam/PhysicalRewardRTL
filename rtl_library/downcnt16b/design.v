// 16-bit down-counter.
module downcnt16b (
    input  wire clk, rst_n,
    output reg  [15:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= {16{1'b1}};
        else        count <= count - 16'd1;
    end
endmodule
