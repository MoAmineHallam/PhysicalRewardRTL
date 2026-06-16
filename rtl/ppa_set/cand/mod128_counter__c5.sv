module mod128_counter__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 7'h00;
    end
    else begin
        count <= (count == 7'h7F) ? 7'h00 : count + 1;
    end
end

endmodule