// 14-bit counter, increments by 10 each cycle.
module step10_cnt14b (
    input  wire clk, rst_n,
    output reg  [13:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 14'd0;
        else        count <= count + 14'd10;
    end
endmodule
