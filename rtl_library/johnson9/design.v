// 9-bit Johnson (twisted-ring) counter.
module johnson9 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'b0;
        else        count <= {count[7:0], ~count[8]};
    end
endmodule
