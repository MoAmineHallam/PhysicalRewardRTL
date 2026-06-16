module mod8_counter__c3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 3'b0; // reset count to 0
    end else begin
        // increment count by 1
        count <= count + 1;
        if (count == 3'b111) begin
            count <= 3'b0; // reset count to 0
        end
    end
end

endmodule