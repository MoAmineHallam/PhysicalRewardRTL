module counter9b__base__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [8:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n)
        count <= 9'b0;
    else
        count <= count + 1;
end

endmodule