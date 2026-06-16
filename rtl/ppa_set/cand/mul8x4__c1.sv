module mul8x4__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [3:0] b,
    output reg  [11:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        product <= 12'b0;
    end else begin
        product <= a * b;
    end
end

endmodule