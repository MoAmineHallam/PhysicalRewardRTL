module counter14b__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n)
begin
    if (!rst_n) // active-low synchronous reset
        count <= 0;
    else // active-high synchronous count
        count <= count + 1;
end

endmodule