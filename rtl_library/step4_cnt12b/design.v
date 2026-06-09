// 12-bit counter, increments by 4 each cycle.
module step4_cnt12b (
    input  wire clk, rst_n,
    output reg  [11:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 12'd0;
        else        count <= count + 12'd4;
    end
endmodule
