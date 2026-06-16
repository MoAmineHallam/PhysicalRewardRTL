module counter5b__c1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (!rst_n) begin
            count <= 5'b0; // reset count to 0
        end else begin
            count <= count + 1; // increment count
        end
    end

endmodule