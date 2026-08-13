module mod32_counter__v4_s100__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n) // active-low reset
        count <= 5'b0; // count <= 0
    else // posedge clk
        count <= count + 1;
end

endmodule