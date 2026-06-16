module step4_cnt8b__c0 (
    input  wire clk, rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else begin
        if (count == 8'b1111_1111) begin
            count <= 8'b0000_0000;
        end else begin
            count <= count + 4'b0100;
        end
    end
end

endmodule