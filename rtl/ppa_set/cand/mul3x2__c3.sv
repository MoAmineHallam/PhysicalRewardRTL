module mul3x2__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [1:0] b,
    output reg  [4:0] product
);

always @(posedge clk) begin
    if (rst_n == 0) begin
        product <= 0;
    end else begin
        product <= a * b;
    end
end

endmodule