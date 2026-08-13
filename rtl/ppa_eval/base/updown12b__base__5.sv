module updown12b__base__5 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [11:0] count
);

always @(posedge clk)
begin
    if (!rst_n)  // Active-low reset
        count <= 12'b0;
    else
        if (dir == 0)  // Counter is counting up
            count <= count + 1;
        else  // Counter is counting down
            count <= count - 1;
end

endmodule