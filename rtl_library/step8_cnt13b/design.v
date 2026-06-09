// 13-bit counter, increments by 8 each cycle.
module step8_cnt13b (
    input  wire clk, rst_n,
    output reg  [12:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 13'd0;
        else        count <= count + 13'd8;
    end
endmodule
