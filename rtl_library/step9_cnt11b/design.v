// 11-bit counter, increments by 9 each cycle.
module step9_cnt11b (
    input  wire clk, rst_n,
    output reg  [10:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 11'd0;
        else        count <= count + 11'd9;
    end
endmodule
