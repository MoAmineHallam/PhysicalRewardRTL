module step8_cnt12b__c0 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
        end else begin
            count <= count + 8;
        end
    end
endmodule