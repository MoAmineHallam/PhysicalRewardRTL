module mul6x6__base__1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [5:0] b,
    output reg  [11:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule