// 6-bit up/down counter. dir=0 up, dir=1 down.
module updown6b (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [5:0] count
);
    always @(posedge clk) begin
        if (!rst_n)   count <= 6'd0;
        else if (dir) count <= count - 6'd1;
        else          count <= count + 6'd1;
    end
endmodule
