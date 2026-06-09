// 15-bit population count (registered).
module popcount15 (
    input  wire clk, rst_n,
    input  wire [14:0] in,
    output reg  [3:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<15;k=k+1) count = count + in[k];
        end
    end
endmodule
