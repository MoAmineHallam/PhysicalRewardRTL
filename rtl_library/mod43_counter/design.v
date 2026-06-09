// Modulo-43 free-running counter (width 6).
module mod43_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 6'd0;
        else if (count == 6'd42) count <= 6'd0;
        else                     count <= count + 6'd1;
    end
endmodule
