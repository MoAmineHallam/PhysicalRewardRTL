module counter7b__v4_s100__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n) // active-low reset
        count <= 7'b0; // reset count to 0
    else
        count <= count + 1; // increment count by 1
end

endmodule