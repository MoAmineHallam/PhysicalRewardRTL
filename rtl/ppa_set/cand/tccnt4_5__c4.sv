module tccnt4_5__c4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count,
    output reg  tc
);

    always @(posedge clk) begin
        if (rst_n == 0) begin
            count <= 4'b0;
            tc <= 0;
        end else begin
            if (count == 4'b101) begin
                count <= 4'b0;
                tc <= 1;
            end else begin
                count <= count + 1;
                tc <= 0;
            end
        end
    end

endmodule