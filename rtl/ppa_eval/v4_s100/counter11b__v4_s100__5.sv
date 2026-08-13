module counter11b__v4_s100__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [10:0] count
);

always @(posedge clk or negedge rst_n)
    if (~rst_n) 
        count <= 11'b0;
    else 
        count <= count + 1;

endmodule