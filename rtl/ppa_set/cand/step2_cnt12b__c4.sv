module step2_cnt12b__c4 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        count <= count + 12'b10;
    end
end

endmodule