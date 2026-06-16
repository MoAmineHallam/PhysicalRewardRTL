module step7_cnt12b__c4 (
    input  wire clk, rst_n,
    output reg  [11:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            count <= 12'h000;
        end else begin
            count <= count + 7;
        end
    end

endmodule