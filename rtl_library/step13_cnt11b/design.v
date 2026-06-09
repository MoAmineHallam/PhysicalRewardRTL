// 11-bit counter, increments by 13 each cycle.
module step13_cnt11b (
    input  wire clk, rst_n,
    output reg  [10:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 11'd0;
        else        count <= count + 11'd13;
    end
endmodule
