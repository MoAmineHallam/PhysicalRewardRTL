module step2_cnt9b__c1 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 0;
    end else begin
        if (count == 9'd511) begin
            count <= 0;
        end else begin
            count <= count + 9'd2;
        end
    end
end

endmodule