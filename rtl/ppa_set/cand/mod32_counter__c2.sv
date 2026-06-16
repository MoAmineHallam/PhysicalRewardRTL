module mod32_counter__c2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 0;
    end else if (count == 31) begin
        count <= 0;
    end else begin
        count <= count + 1;
    end
end

endmodule