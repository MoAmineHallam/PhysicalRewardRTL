module counter10b__v4_s100__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n)
        count <= 10'b0;
    else
        count <= count + 1;
end

endmodule