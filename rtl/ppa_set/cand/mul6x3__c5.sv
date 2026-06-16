module mul6x3__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [5:0] a,
    input  wire [2:0] b,
    output reg  [8:0] product
);

always @(posedge clk)
    if (~rst_n) begin
        product <= 9'b0;
    end else begin
        product <= a * b;
    end

endmodule