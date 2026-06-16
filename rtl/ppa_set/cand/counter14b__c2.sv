module counter14b__c2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if(!rst_n) // synchronous active-low reset
        count <= 0;
    else
        count <= count + 1;
end

endmodule