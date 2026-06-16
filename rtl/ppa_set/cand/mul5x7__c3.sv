module mul5x7__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [6:0] b,
    output reg  [11:0] product
);

always @(posedge clk, negedge rst_n)
begin
    if (!rst_n)
        product <= 0;
    else
        product <= a * b;
end

endmodule