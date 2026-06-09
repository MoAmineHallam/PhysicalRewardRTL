// 5-bit population count (registered).
module popcount5 (
    input  wire clk, rst_n,
    input  wire [4:0] in,
    output reg  [2:0] count
);
    integer k;
    always @(posedge clk) begin
        if (!rst_n) count <= 0;
        else begin
            count = 0;
            for (k=0;k<5;k=k+1) count = count + in[k];
        end
    end
endmodule
