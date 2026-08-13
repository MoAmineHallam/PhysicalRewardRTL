module counter14b__v4_s100__6 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (rst_n == 0)
        count <= 0;
    else
        count <= count + 1;
end

endmodule