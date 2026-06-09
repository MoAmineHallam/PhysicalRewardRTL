// 3-bit Johnson (twisted-ring) counter.
module johnson3 (
    input  wire clk, rst_n,
    output reg  [2:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 3'b0;
        else        count <= {count[1:0], ~count[2]};
    end
endmodule
