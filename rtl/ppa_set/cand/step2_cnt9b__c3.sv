module step2_cnt9b__c3 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);

always @(posedge clk, negedge rst_n)
begin
    if (!rst_n)
        count <= 9'b0;
    else
        count <= count + 2'd2;
end

endmodule