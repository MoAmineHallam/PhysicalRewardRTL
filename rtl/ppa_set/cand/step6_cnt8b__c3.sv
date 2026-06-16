module step6_cnt8b__c3 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if(~rst_n) begin
        count <= 8'b0;
    end else begin
        count <= count + 6;
    end
end

endmodule