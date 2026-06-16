module mul6x2__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [1:0] b,
    output reg  [7:0] product
);

always @(posedge clk)
begin
    if (!rst_n) // active low
        product <= 8'b0;
    else // active high
        product <= a * b;
end

endmodule