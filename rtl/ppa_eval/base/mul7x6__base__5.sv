module mul7x6__base__5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [5:0] b,
    output reg  [12:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a*b;
    end
end

endmodule