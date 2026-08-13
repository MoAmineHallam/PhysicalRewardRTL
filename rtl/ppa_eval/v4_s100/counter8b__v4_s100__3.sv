module counter8b__v4_s100__3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n) // active-low reset
        count <= 8'b0;
    else // active-high count
        count <= count + 1;
end

endmodule