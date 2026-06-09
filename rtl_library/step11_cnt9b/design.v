// 9-bit counter, increments by 11 each cycle.
module step11_cnt9b (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'd0;
        else        count <= count + 9'd11;
    end
endmodule
