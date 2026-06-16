module mul5x7__c2 (
    input clk,
    input rst_n,
    input [4:0] a,
    input [6:0] b,
    output reg [11:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        product <= 12'b0;
    end else begin
        product <= a * b;
    end
end

endmodule