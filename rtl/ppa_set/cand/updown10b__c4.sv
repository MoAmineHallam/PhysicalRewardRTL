module updown10b__c4 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 10'b0;
    end else begin
        if (dir == 1'b0) begin
            count <= count + 10'b1;
        end else begin
            count <= count - 10'b1;
        end
    end
end

endmodule