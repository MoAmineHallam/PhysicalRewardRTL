module mod170_counter__c1 (
    input wire clk,
    input wire rst_n,
    output reg [7:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 8'h00;
    end else begin
        if (count == 8'hA9) begin
            count <= 8'h00;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule