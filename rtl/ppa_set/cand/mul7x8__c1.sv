module mul7x8__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire [6:0] a,
    input  wire [7:0] b,
    output reg  [14:0] product
);

always @(posedge clk or negedge rst_n) begin
    if(!rst_n) begin
        product <= 15'b0;
    end else begin
        product <= a * b;
    end
end

endmodule