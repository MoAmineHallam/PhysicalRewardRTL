module counter14b__c3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

    always @(posedge clk or negedge rst_n)
    begin
        if (!rst_n)
            count <= 14'b0;
        else
            count <= count + 1;
    end

endmodule