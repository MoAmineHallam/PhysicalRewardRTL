module counter14b__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'b0;
    end else begin
        if (count == 14'h3fff) begin
            count <= 14'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule