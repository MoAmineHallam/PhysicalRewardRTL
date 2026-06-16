module step2_cnt8b__c5 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'b0;
    end
    else if (count == 8'd255) begin
        count <= 8'b0;
    end
    else begin
        count <= count + 8'd2;
    end
end

endmodule