module mul8x2__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [1:0] b,
    output reg  [9:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule