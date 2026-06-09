// 12-bit Johnson (twisted-ring) counter.
module johnson12 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'b0;
        else        count <= {count[10:0], ~count[11]};
    end
endmodule
