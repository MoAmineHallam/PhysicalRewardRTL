module counter12b__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [11:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            count <= 12'h000;
        end
        else begin
            count <= count + 1;
        end
    end

endmodule