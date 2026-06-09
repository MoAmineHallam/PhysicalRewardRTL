// 4-bit counter, increments by 6 each cycle.
module step6_cnt4b (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'd0;
        else        count <= count + 4'd6;
    end
endmodule
