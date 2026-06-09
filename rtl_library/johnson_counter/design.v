// 4-bit Johnson (twisted ring) counter. Period = 8.
// Sequence: 0000->0001->0011->0111->1111->1110->1100->1000->0000
module johnson_counter (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'b0000;
        else        count <= {count[2:0], ~count[3]};
    end
endmodule
