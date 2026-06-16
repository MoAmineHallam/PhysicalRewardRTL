module step15_cnt8b__c4 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 8'b0;
        end
        else begin
            count <= count + 8'd15;
        end
    end

endmodule