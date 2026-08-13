module counter16b__v4_s100__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n) // active-low reset
        count <= 16'b0;
    else // active-high increment
        count <= count + 16'b1;
end

endmodule