module counter13b__c3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [12:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 13'b0;
        end else begin
            if (count == 13'h1FFF) begin
                count <= 13'b0;
            end else begin
                count <= count + 1;
            end
        end
    end

endmodule