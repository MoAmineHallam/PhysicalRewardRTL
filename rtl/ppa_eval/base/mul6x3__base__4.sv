module mul6x3__base__4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [2:0] b,
    output reg  [8:0] product
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule