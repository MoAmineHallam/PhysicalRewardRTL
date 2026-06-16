module updown3b__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [2:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 3'b0;
    end else if (dir) begin
        count <= count - 1;
    end else begin
        count <= count + 1;
    end
end

endmodule