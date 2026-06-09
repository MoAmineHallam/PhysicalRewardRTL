// 4-bit counter, increments by 5 each cycle.
module step5_cnt4b (
    input  wire clk, rst_n,
    output reg  [3:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 4'd0;
        else        count <= count + 4'd5;
    end
endmodule
