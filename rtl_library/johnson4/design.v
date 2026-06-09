// 4-bit Johnson (twisted-ring) counter.
module johnson4 (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'b0;
        else        count <= {count[2:0], ~count[3]};
    end
endmodule
