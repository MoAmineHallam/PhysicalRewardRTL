module step7_cnt12b__c2 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk) begin
    if (rst_n == 1'b0) begin
        count <= 12'h000;
    end
    else begin
        count <= count + 12'h007;
    end
end

endmodule