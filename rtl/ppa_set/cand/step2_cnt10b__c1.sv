module step2_cnt10b__c1 (
    input  wire clk, rst_n,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 10'b0;
    end else begin
        count <= count + 10'b10;
    end
end

endmodule