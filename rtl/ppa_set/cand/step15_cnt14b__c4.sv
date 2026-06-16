module step15_cnt14b__c4 (
    input  wire clk, rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'h0000;
    end else begin
        count <= count + 15;
    end
end

endmodule