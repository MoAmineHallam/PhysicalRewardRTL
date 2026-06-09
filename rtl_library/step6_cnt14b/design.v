// 14-bit counter, increments by 6 each cycle.
module step6_cnt14b (
    input  wire clk, rst_n,
    output reg  [13:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 14'd0;
        else        count <= count + 14'd6;
    end
endmodule
