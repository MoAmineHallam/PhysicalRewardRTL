module mul5x6__base__2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [5:0] b,
    output reg  [10:0] product
);

    always @ (posedge clk or negedge rst_n) begin
        if (!rst_n)
            product <= 0;
        else
            product <= a*b;
    end

endmodule