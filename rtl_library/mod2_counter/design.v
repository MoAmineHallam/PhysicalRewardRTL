// Modulo-2 free-running counter (width 1).
module mod2_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 1'd0;
        else if (count == 1'd1) count <= 1'd0;
        else                     count <= count + 1'd1;
    end
endmodule
