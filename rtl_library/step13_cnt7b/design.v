// 7-bit counter, increments by 13 each cycle.
module step13_cnt7b (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'd0;
        else        count <= count + 7'd13;
    end
endmodule
