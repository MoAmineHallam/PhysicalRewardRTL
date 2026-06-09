// 6-bit counter, increments by 13 each cycle.
module step13_cnt6b (
    input  wire clk, rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 6'd0;
        else        count <= count + 6'd13;
    end
endmodule
