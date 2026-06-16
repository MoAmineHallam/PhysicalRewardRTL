module counter16b__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 16'h0000;
    end else begin
        if (count == 16'hFFFF) begin
            count <= 16'h0000;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule