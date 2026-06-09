// 13-bit parity (registered): even = ^in.
module parity13 (
    input  wire clk, rst_n,
    input  wire [12:0] in,
    output reg  even, odd
);
    always @(posedge clk) begin
        if (!rst_n) begin even<=0; odd<=1; end
        else begin even <= ^in; odd <= ~(^in); end
    end
endmodule
