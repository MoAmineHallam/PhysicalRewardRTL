module step9_cnt7b__c5 (
    input  wire clk, rst_n,
    output reg  [6:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 7'd0;
    end else begin
        count <= count + 7'd9;
    end
end

endmodule