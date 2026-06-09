// 10-bit counter, increments by 4 each cycle.
module step4_cnt10b (
    input  wire clk, rst_n,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 10'd0;
        else        count <= count + 10'd4;
    end
endmodule
