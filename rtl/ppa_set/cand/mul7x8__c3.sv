module mul7x8__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [7:0] b,
    output reg  [14:0] product
);

reg [14:0] prod_reg;

always @(posedge clk) begin
    if (!rst_n) begin
        prod_reg <= 0;
    end else begin
        prod_reg <= a * b;
    end
end

assign product = prod_reg;

endmodule