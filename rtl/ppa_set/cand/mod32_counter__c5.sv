module mod32_counter__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 5'b00000;
        end
        else begin
            if (count == 5'b11111) begin
                count <= 5'b00000;
            end
            else begin
                count <= count + 1;
            end
        end
    end

endmodule