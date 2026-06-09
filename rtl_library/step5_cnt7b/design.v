// 7-bit counter, increments by 5 each cycle.
module step5_cnt7b (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'd0;
        else        count <= count + 7'd5;
    end
endmodule
