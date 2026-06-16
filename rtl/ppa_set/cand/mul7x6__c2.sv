module mul7x6__c2 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [5:0] b,
    output reg  [12:0] product
);

always @(posedge clk) begin
    if (!rst_n) begin
        product <= 13'b0;
    end else begin
        product <= a * b;
    end
end

endmodule