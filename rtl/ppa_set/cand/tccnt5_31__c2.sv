module tccnt5_31__c2 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

always @(posedge clk) begin
    if (~rst_n) begin
        count <= 5'b0;
        tc <= 1'b0;
    end else begin
        if (count == 5'd31) begin
            count <= 5'b0;
            tc <= 1'b1;
        end else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end
end

endmodule