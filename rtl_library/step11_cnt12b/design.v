// 12-bit counter, increments by 11 each cycle.
module step11_cnt12b (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'd0;
        else        count <= count + 12'd11;
    end
endmodule
