// 8-bit counter, increments by 10 each cycle.
module step10_cnt8b (
    input  wire clk, rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 8'd0;
        else        count <= count + 8'd10;
    end
endmodule
