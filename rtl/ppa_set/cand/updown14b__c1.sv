module updown14b__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [13:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'h0000;
    end else begin
        if (dir == 1'b1) begin
            count <= count - 1;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule