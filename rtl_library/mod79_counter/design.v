// Modulo-79 free-running counter (width 7).
module mod79_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 7'd0;
        else if (count == 7'd78) count <= 7'd0;
        else                     count <= count + 7'd1;
    end
endmodule
