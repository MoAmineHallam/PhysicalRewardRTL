module mod170_counter__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 8'd0;
    end else if (count == 8'd169) begin
        count <= 8'd0;
    end else begin
        count <= count + 8'd1;
    end
end

endmodule