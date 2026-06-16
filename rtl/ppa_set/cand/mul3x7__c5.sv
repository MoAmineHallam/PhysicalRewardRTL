module mul3x7__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] a,
    input  wire [6:0] b,
    output reg  [9:0] product
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        product <= 10'b0;
    end else begin
        product <= a * b;
    end
end

endmodule