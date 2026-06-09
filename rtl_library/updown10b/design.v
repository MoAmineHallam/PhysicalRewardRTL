// 10-bit up/down counter. dir=0 up, dir=1 down.
module updown10b (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [9:0] count
);
    always @(posedge clk) begin
        if (!rst_n)   count <= 10'd0;
        else if (dir) count <= count - 10'd1;
        else          count <= count + 10'd1;
    end
endmodule
