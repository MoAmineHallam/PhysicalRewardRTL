module step9_cnt7b__c3 (
    input  wire clk, rst_n,
    output reg  [6:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 7'b0;
    end else begin
        count <= count + 7'd9;
    end
end

endmodule