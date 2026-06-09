// 6-bit Johnson (twisted-ring) counter.
module johnson6 (
    input  wire clk, rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 6'b0;
        else        count <= {count[4:0], ~count[5]};
    end
endmodule
