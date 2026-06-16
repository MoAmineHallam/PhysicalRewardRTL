module updown10b__c3 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 10'd0;
    end else begin
        if (dir) begin
            count <= count - 1'b1;
        end else begin
            count <= count + 1'b1;
        end
    end
end

endmodule