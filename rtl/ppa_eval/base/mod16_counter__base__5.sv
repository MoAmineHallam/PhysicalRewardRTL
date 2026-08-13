module mod16_counter__base__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n)
        count <= 4'b0000;
    else
        count <= (count == 4'b1111) ? 4'b0000 : count + 1;
end

endmodule