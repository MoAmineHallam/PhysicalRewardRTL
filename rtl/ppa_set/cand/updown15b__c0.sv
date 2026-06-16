module updown15b__c0 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [14:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        count <= 15'b0;
    end
    else begin
        if (dir == 0) begin
            count <= count + 2'b01;
        end
        else begin
            count <= count - 2'b01;
        end
    end
end

endmodule