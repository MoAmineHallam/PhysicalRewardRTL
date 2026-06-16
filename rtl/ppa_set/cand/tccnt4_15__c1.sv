module tccnt4_15__c1 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);

always @(posedge clk) begin
    if (~rst_n) begin
        count <= 4'd0;
        tc <= 1'b0;
    end
    else begin
        if (count == 4'd15) begin
            count <= 4'd0;
            tc <= 1'b1;
        end
        else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end
end

endmodule