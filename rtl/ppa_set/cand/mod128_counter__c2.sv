module mod128_counter__c2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 7'b0;
    end else begin
        if (count == 7'b1111111) begin
            count <= 7'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule