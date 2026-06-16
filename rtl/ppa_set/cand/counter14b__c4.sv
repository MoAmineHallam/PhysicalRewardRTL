module counter14b__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'h0000;
    end else begin
        count <= count + 1;
    end
end

endmodule