module mod170_counter__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
        end
        else begin
            if (count == 169) begin
                count <= 0;
            end
            else begin
                count <= count + 1;
            end
        end
    end

endmodule