module counter15b__base__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [14:0] count
);

always @(posedge clk, negedge rst_n)
begin
    if (~rst_n)
        count <= 15'b0;
    else
        count <= count + 1;
end

endmodule