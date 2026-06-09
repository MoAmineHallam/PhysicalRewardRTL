// 9-bit binary up-counter.
module counter9b (
    input  wire clk,
    input  wire rst_n,
    output reg  [8:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 9'd0;
        else        count <= count + 9'd1;
    end
endmodule
