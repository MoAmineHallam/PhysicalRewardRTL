module step2_cnt9b__c5 (
    input  wire clk, rst_n,
    output reg  [8:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            count <= 9'd0;
        end
        else begin
            count <= count + 9'd2;
        end
    end

endmodule