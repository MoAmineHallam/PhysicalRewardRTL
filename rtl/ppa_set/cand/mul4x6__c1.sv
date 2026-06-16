module mul4x6__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [5:0] b,
    output reg  [9:0] product
);

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n)
        product <= 10'b0;
    else
        product <= a * b;
end

endmodule