module mul4x6__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [5:0] b,
    output reg  [9:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (rst_n == 1'b0) begin
        product <= 10'h000;
    end else begin
        product <= a * b;
    end
end

endmodule