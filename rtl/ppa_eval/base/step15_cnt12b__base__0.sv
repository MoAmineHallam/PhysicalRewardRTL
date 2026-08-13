module step15_cnt12b__base__0 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk or negedge rst_n)
    if (!rst_n)
        count <= 12'b0;
    else
        count <= count + 15;

endmodule