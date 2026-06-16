module tccnt5_10__c1 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 5'b0;
        tc <= 1'b0;
    end else begin
        if (count == 5'b1010) begin
            count <= 5'b0;
            tc <= 1'b1;
        end else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end
end

endmodule