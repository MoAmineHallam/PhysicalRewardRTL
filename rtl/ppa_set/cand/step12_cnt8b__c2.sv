module step12_cnt8b__c2 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else begin
        count <= count + 8'd12;
    end
end

endmodule