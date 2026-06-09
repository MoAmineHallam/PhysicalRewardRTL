// 12-bit population count (registered).
module popcount12 (
    input  wire clk, rst_n,
    input  wire [11:0] in,
    output reg  [3:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<12;k=k+1) count = count + in[k];
        end
    end
endmodule
