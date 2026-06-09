// Modulo-7 free-running counter (width 3).
module mod7_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 3'd0;
        else if (count == 3'd6) count <= 3'd0;
        else                     count <= count + 3'd1;
    end
endmodule
