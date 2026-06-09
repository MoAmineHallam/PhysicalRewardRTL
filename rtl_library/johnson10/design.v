// 10-bit Johnson (twisted-ring) counter.
module johnson10 (
    input  wire clk, rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 10'b0;
        else        count <= {count[8:0], ~count[9]};
    end
endmodule
