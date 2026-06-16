module step2_cnt11b__c1 (
    input  wire clk, rst_n,
    output reg  [10:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
    end else begin
        count <= count + 2;
    end
end

endmodule