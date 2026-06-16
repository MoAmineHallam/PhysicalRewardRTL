module step7_cnt12b__c3 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

always @(posedge clk, negedge rst_n)
    if (!rst_n)
        count <= 0;
    else
        count <= count + 7;

endmodule