module satadd12b__c4 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

reg [11:0] tmp;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        tmp <= 12'b0;
        sum <= 12'b0;
    end else begin
        tmp <= a + b;
        if (tmp > 12'hFFF) begin
            sum <= 12'hFFF;
        end else begin
            sum <= tmp;
        end
    end
end

endmodule