// 4-bit counter, increments by 10 each cycle.
module step10_cnt4b (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'd0;
        else        count <= count + 4'd10;
    end
endmodule
