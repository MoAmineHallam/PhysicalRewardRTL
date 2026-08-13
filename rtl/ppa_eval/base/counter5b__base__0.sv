module counter5b__base__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n)    // synchronous reset
        count <= 5'b0;
    else
        count <= count + 1;
end

endmodule