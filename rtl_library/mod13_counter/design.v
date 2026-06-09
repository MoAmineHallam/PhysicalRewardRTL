// Modulo-13 free-running counter (width 4).
module mod13_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 4'd0;
        else if (count == 4'd12) count <= 4'd0;
        else                     count <= count + 4'd1;
    end
endmodule
