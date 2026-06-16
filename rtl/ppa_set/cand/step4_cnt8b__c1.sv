module step4_cnt8b__c1 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n)
        count <= 8'b0;
    else
        count <= count + 4;
end

endmodule