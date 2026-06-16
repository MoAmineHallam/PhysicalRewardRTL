module satadd12b__c0 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        sum <= 12'b0;
    end else begin
        if (a + b > 12'd4095) begin
            sum <= 12'd4095;
        end else if (a + b < 12'd0) begin
            sum <= 12'd0;
        end else begin
            sum <= a + b;
        end
    end
end

endmodule