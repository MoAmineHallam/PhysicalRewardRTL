module mul8x4__c4 (
    input clk,
    input rst_n,
    input [7:0] a,
    input [3:0] b,
    output reg [11:0] product
);

    always @(posedge clk) begin
        if (!rst_n) begin
            product <= 0;
        end else begin
            product <= a * b;
        end
    end

endmodule