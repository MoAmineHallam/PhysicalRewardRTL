// Modulo-184 free-running counter (width 8).
module mod184_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 8'd0;
        else if (count == 8'd183) count <= 8'd0;
        else                     count <= count + 8'd1;
    end
endmodule
