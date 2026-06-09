// 3-bit population count (registered).
module popcount3 (
    input  wire clk, rst_n,
    input  wire [2:0] in,
    output reg  [1:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<3;k=k+1) count = count + in[k];
        end
    end
endmodule
