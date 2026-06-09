// 10-bit counter, increments by 8 each cycle.
module step8_cnt10b (
    input  wire clk, rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 10'd0;
        else        count <= count + 10'd8;
    end
endmodule
