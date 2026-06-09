// 8-bit Johnson (twisted-ring) counter.
module johnson8 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 8'b0;
        else        count <= {count[6:0], ~count[7]};
    end
endmodule
