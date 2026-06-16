module mul6x6__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [5:0] b,
    output reg  [11:0] product
);

reg [11:0] prod_reg;

always @(posedge clk) begin
    if (!rst_n) begin
        prod_reg <= 0;
    end else begin
        prod_reg <= a * b;
    end
end

assign product = prod_reg;

endmodule