module mul8x5__c4 (
    input  wire clk,
    input  wire rst_n,
    input  wire [7:0] a,
    input  wire [4:0] b,
    output reg  [12:0] product
);
    
    always @(posedge clk) begin
        if(!rst_n) begin
            product <= 13'b0;
        end else begin
            product <= {1'b0, a} * {1'b0, b};
        end
    end

endmodule