// Shift-accumulate: accum = (accum + data) >> 1 each cycle (logical shift).
module shift_accum (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [3:0] data,
    output reg  [7:0] accum
);
    always @(posedge clk) begin
        if (!rst_n) accum <= 8'b0;
        else        accum <= (accum + {4'b0, data}) >> 1;
    end
endmodule
