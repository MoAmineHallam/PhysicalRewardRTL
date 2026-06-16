module updown8b__c0 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [7:0] count
);

always @(posedge clk)
begin
    if (!rst_n) begin
        count <= 8'b0;
    end
    else if (dir == 1'b1) begin
        count <= count - 1;
    end
    else begin
        count <= count + 1;
    end
end

endmodule