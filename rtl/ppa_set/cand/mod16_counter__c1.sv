module mod16_counter__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 4'b0000;
    end else begin
        count <= (count == 4'b1111) ? 4'b0000 : count + 1;
    end
end

endmodule