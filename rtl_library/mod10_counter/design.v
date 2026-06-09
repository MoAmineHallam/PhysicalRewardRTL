// Modulo-10 (decade) counter. Free-runs: 0,1,...,9,0,...
// No external inputs beyond clk/rst_n.
// Period = 10. Probed as {12'b0, count[3:0]}.
module mod10_counter (
    input  wire       clk,
    input  wire       rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n)        count <= 4'd0;
        else if (count == 4'd9) count <= 4'd0;
        else               count <= count + 4'd1;
    end
endmodule
