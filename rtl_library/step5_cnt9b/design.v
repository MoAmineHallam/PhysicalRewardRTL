// 9-bit counter, increments by 5 each cycle.
module step5_cnt9b (
    input  wire clk, rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'd0;
        else        count <= count + 9'd5;
    end
endmodule
