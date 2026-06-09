// 12-bit counter, increments by 10 each cycle.
module step10_cnt12b (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'd0;
        else        count <= count + 12'd10;
    end
endmodule
