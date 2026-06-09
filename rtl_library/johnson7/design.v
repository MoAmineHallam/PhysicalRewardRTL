// 7-bit Johnson (twisted-ring) counter.
module johnson7 (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'b0;
        else        count <= {count[5:0], ~count[6]};
    end
endmodule
