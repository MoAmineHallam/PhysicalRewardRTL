module tccnt4_5__c2 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 4'b0;
            tc <= 1'b0;
        end
        else if (count == 4'b101) begin
            count <= 4'b0;
            tc <= 1'b1;
        end
        else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end

endmodule