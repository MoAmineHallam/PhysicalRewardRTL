module satadd12b__c3 (
    input  wire clk, rst_n,
    input  wire [11:0] a,
    input  wire [11:0] b,
    output reg  [11:0] sum
);

reg [11:0] temp_sum;

always @ (posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        temp_sum <= 0;
    end else begin
        temp_sum <= a + b;
    end
end

assign sum = (temp_sum > 12'hfff) ? 12'hfff : temp_sum;

endmodule