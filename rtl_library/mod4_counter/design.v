// Modulo-4 free-running counter (width 2).
module mod4_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [1:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 2'd0;
        else if (count == 2'd3) count <= 2'd0;
        else                     count <= count + 2'd1;
    end
endmodule
