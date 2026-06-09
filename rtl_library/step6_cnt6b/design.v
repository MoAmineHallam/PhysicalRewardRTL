// 6-bit counter, increments by 6 each cycle.
module step6_cnt6b (
    input  wire clk, rst_n,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 6'd0;
        else        count <= count + 6'd6;
    end
endmodule
