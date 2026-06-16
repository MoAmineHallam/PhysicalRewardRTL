module mod256_counter__c5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin // active-low reset
        count <= 8'd0; // reset count to 0
    end
    else begin
        if (count == 8'd255) begin // if count is at max value
            count <= 8'd0; // reset count to 0
        end
        else begin
            count <= count + 1; // increment count
        end
    end
end

endmodule