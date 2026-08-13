module step2_cnt10b__base__2 (
    input  wire clk, rst_n,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n)
    if (!rst_n)
       count <= 10'b0;
    else
       count <= count + 10'b10;

endmodule