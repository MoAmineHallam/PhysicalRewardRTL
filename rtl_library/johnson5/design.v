// 5-bit Johnson (twisted-ring) counter.
module johnson5 (
    input  wire clk, rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 5'b0;
        else        count <= {count[3:0], ~count[4]};
    end
endmodule
