module mul4x7__c2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [6:0] b,
    output reg  [10:0] product
);

always @(posedge clk) begin
    if(!rst_n) begin
        product <= 11'b0;
    end
    else begin
        product <= a * b;
    end
end

endmodule