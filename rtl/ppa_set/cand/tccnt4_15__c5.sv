module tccnt4_15__c5 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 0;
            tc <= 0;
        end
        else begin
            if (count == 15) begin
                count <= 0;
                tc <= 1;
            end
            else begin
                count <= count + 1;
                tc <= 0;
            end
        end
    end

endmodule