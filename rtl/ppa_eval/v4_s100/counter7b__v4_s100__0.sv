module counter7b__v4_s100__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

    always @(posedge clk or negedge rst_n)
        if (~rst_n)
            count <= 7'b0;
        else
            count <= count + 1;

endmodule