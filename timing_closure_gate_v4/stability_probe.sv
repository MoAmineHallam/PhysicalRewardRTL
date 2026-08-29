module timing_gate_v4_stability_probe (
    input  wire        clk,
    input  wire [15:0] a,
    input  wire [15:0] b,
    output reg  [16:0] y
);
    reg [16:0] sum_q;
    always @(posedge clk) begin
        sum_q <= {1'b0, a} + {1'b0, b};
        y <= sum_q + 17'd1;
    end
endmodule
