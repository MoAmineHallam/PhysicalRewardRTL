module step2_cnt9b__c0 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);

always @(posedge clk)
begin
    if (!rst_n)
        count <= 9'd0;
    else
        count <= count + 9'd2;
end

endmodule