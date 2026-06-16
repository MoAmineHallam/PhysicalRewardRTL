module counter16b__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);
    always @(posedge clk, negedge rst_n) begin
        if (~rst_n) begin
            count <= 16'b0;
        end else begin
            count <= (count == 16'hffff) ? 16'b0 : count + 1;
        end
    end
endmodule