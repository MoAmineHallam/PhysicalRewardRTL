module counter9b__c3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [8:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
    end else begin
        if (count == 9'h1FF) begin
            count <= 0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule