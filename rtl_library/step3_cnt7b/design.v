// 7-bit counter, increments by 3 each cycle.
module step3_cnt7b (
    input  wire clk, rst_n,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 7'd0;
        else        count <= count + 7'd3;
    end
endmodule
