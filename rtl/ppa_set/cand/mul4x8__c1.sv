module mul4x8__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [7:0] b,
    output reg  [11:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule