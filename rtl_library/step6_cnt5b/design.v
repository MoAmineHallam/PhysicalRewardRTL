// 5-bit counter, increments by 6 each cycle.
module step6_cnt5b (
    input  wire clk, rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 5'd0;
        else        count <= count + 5'd6;
    end
endmodule
