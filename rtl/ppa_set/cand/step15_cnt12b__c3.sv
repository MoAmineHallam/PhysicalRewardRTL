module step15_cnt12b__c3 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        count <= count + 15;
    end
end

endmodule