// 13-bit binary up-counter.
module counter13b (
    input  wire clk,
    input  wire rst_n,
    output reg  [12:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 13'd0;
        else        count <= count + 13'd1;
    end
endmodule
