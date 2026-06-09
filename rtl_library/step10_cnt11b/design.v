// 11-bit counter, increments by 10 each cycle.
module step10_cnt11b (
    input  wire clk, rst_n,
    output reg  [10:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 11'd0;
        else        count <= count + 11'd10;
    end
endmodule
