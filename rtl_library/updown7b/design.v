// 7-bit up/down counter. dir=0 up, dir=1 down.
module updown7b (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [6:0] count
);
    always @(posedge clk) begin
        if (!rst_n)   count <= 7'd0;
        else if (dir) count <= count - 7'd1;
        else          count <= count + 7'd1;
    end
endmodule
