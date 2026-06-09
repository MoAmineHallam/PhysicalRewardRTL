// 9-bit counter, increments by 9 each cycle.
module step9_cnt9b (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'd0;
        else        count <= count + 9'd9;
    end
endmodule
