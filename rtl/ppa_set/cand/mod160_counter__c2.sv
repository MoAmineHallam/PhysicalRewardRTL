module mod160_counter__c2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'h00;
    end
    else begin
        count <= (count == 8'h9f) ? 8'h00 : count + 1;
    end
end

endmodule