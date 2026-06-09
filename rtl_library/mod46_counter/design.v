// Modulo-46 free-running counter (width 6).
module mod46_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 6'd0;
        else if (count == 6'd45) count <= 6'd0;
        else                     count <= count + 6'd1;
    end
endmodule
