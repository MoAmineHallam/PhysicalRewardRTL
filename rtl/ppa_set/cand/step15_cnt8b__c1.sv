module step15_cnt8b__c1 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'h00;
    end else begin
        count <= count + 8'h0F;
    end
end

endmodule