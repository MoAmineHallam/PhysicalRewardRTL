module mul5x5__c4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [4:0] a,
    input  wire [4:0] b,
    output reg  [9:0] product
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        product <= 10'b0;
    end else begin
        product <= a * b;
    end
end

endmodule