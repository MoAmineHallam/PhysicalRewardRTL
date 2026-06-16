module tccnt5_10__c0 (
    input  wire clk, rst_n,
    output reg  [4:0] count,
    output reg  tc
);

    always@(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            count <= 0;
            tc <= 0;
        end
        else if (count == 5'b1010) begin
            count <= 0;
            tc <= 1;
        end
        else begin
            count <= count + 1;
            tc <= 0;
        end
    end

endmodule