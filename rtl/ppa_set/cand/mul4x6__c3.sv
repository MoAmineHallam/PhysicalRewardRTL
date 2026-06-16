module mul4x6__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire [3:0] a,
    input  wire [5:0] b,
    output reg  [9:0] product
);

    always @(posedge clk, negedge rst_n) begin
        if(!rst_n) begin
            product <= 0;
        end
        else begin
            product <= a * b;
        end
    end

endmodule