module mul8x5__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [4:0] b,
    output reg  [12:0] product
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        product <= 0;
    end
    else begin
        product <= a * b;
    end
end

endmodule