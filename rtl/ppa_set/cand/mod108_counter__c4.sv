module mod108_counter__c4 (
    input wire clk,
    input wire rst_n,
    output reg [6:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 7'd0;
    end else begin
        count <= count + 7'd1;
        if (count == 7'd107) begin
            count <= 7'd0;
        end
    end
end

endmodule