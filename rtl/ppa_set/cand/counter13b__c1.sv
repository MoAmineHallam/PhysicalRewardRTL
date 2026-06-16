module counter13b__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [12:0] count
);

    always @(posedge clk or negedge rst_n)
    begin
        if (~rst_n)
            count <= 0;
        else
            count <= count + 1;
    end

endmodule