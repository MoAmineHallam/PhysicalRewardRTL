// Modulo-18 free-running counter (width 5).
module mod18_counter (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n)              count <= 5'd0;
        else if (count == 5'd17) count <= 5'd0;
        else                     count <= count + 5'd1;
    end
endmodule
