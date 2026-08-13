module mod2_counter__v4_s100__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n)
        count <= 1'b0;
    else
        count <= ~count;
end

endmodule