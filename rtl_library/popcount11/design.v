// 11-bit population count (registered).
module popcount11 (
    input  wire clk, rst_n,
    input  wire [10:0] in,
    output reg  [3:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<11;k=k+1) count = count + in[k];
        end
    end
endmodule
