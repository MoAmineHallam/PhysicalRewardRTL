// 13-bit counter, increments by 13 each cycle.
module step13_cnt13b (
    input  wire clk, rst_n,
    output reg  [12:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 13'd0;
        else        count <= count + 13'd13;
    end
endmodule
