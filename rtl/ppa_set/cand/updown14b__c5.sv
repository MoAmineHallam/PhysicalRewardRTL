module updown14b__c5 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'b0;
    end else if (dir) begin
        count <= count - 14'b1;
    end else begin
        count <= count + 14'b1;
    end
end

endmodule