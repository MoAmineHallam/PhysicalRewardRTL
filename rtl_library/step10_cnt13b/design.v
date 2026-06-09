// 13-bit counter, increments by 10 each cycle.
module step10_cnt13b (
    input  wire clk, rst_n,
    output reg  [12:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 13'd0;
        else        count <= count + 13'd10;
    end
endmodule
