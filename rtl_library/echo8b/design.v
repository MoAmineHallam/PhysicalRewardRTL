// Canary DUT for the silicon-Fmax feasibility spike: a 3-deep flip-flop chain
// that echoes the 8-bit input with NO combinational logic between registers.
// Its register-to-register path is essentially zero, so it runs far faster
// than any real design (>400 MHz on xc7z020-1).  It is packed in the SAME
// bitstream as the design under test and shares the sel-mux -> LA-buffer ->
// AXI-readback tail; therefore if the canary still matches its golden at clock
// frequency f, the capture infrastructure is sound at f, and any failure of
// the design-under-test at f is the DUT's own timing -- not the harness.
module echo8b (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] d0, d1;
    always @(posedge clk) begin
        if (!rst_n) begin
            d0 <= 8'd0; d1 <= 8'd0; y <= 16'd0;
        end else begin
            d0 <= x;
            d1 <= d0;
            y  <= {8'd0, d1};
        end
    end
endmodule
