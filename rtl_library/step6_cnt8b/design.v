// 8-bit counter, increments by 6 each cycle.
module step6_cnt8b (
    input  wire clk, rst_n,
    output reg  [7:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 8'd0;
        else        count <= count + 8'd6;
    end
endmodule
