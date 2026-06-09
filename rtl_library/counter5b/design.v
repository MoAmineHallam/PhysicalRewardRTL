// 5-bit binary up-counter.
module counter5b (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);
    always @(posedge clk) begin
        if (!rst_n) count <= 5'd0;
        else        count <= count + 5'd1;
    end
endmodule
