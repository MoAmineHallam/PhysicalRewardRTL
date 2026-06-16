module step2_cnt12b__c1 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        count <= count + 12'b10;
        if (count == 12'b111111111111) begin
            count <= 12'b0;
        end
    end
end

endmodule