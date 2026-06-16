module tccnt8_255__c0 (
    input  wire clk, rst_n,
    output reg  [7:0] count,
    output reg  tc
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
        tc <= 1'b0;
    end
    else begin
        if (count == 8'hFF) begin
            tc <= 1'b1;
            count <= 8'b0;
        end
        else begin
            tc <= 1'b0;
            count <= count + 1;
        end
    end
end

endmodule