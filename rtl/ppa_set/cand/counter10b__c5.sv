module counter10b__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n)
    if (~rst_n)
        count <= 10'd0;
    else
        count <= count + 1;
        
endmodule