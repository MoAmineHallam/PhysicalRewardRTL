module updown14b__c0 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 14'b0;
    end else begin
        case (dir)
            1'b0: count <= count + 14'b1; // up
            1'b1: count <= count - 14'b1; // down
        endcase
    end
end

endmodule