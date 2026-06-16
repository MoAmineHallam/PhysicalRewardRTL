module mul2x8__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [7:0] b,
    output reg  [9:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 10'b0;  // clear output
    end else begin
        product <= a * b;  // multiply inputs and assign to output
    end
end

endmodule