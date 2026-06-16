module mod8_counter__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 3'b0;
        end else if (count == 3'b111) begin
            count <= 3'b0;
        end else begin
            count <= count + 1;
        end
    end

endmodule