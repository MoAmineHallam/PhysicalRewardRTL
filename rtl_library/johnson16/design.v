// 16-bit Johnson (twisted-ring) counter.
module johnson16 (
    input  wire clk, rst_n,
    output reg  [15:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 16'b0;
        else        count <= {count[14:0], ~count[15]};
    end
endmodule
