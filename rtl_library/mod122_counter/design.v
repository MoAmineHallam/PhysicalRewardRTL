// Modulo-122 free-running counter (width 7).
module mod122_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 7'd0;
        else if (count == 7'd121) count <= 7'd0;
        else                     count <= count + 7'd1;
    end
endmodule
