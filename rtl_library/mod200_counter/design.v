// Modulo-200 free-running counter (width 8).
module mod200_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 8'd0;
        else if (count == 8'd199) count <= 8'd0;
        else                     count <= count + 8'd1;
    end
endmodule
