// 9-bit counter, increments by 6 each cycle.
module step6_cnt9b (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'd0;
        else        count <= count + 9'd6;
    end
endmodule
