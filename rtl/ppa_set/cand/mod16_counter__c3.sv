module mod16_counter__c3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            count <= 4'b0;
        end
        else begin
            if (count == 4'hF) begin
                count <= 4'b0;
            end
            else begin
                count <= count + 1;
            end
        end
    end

endmodule