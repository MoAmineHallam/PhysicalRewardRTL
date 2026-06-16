module updown4b__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [3:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 4'b0000;
    end else begin
        if (dir == 1'b0) begin
            count <= count + 1;
        end else begin
            count <= count - 1;
        end
    end
end

endmodule