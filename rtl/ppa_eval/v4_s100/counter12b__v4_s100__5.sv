module counter12b__v4_s100__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [11:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n)
        count <= 12'b0;
    else
        count <= count + 1;
end

endmodule