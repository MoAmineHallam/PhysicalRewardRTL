module mul2x6__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire [1:0] a,
    input  wire [5:0] b,
    output reg  [7:0] product
);

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            product <= 0;
        end else begin
            product <= a * b;
        end
    end

endmodule