module counter8b__v4_s100__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n)
    if (!rst_n)  // active-low reset
        count <= 8'b0;
    else
        count <= count + 1;  // free running counter

endmodule