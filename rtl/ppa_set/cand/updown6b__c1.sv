module updown6b__c1 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg [5:0] count
);

    always @(posedge clk) begin
        if (!rst_n) begin
            count <= 6'd0;
        end else if (dir == 1'b1) begin
            count <= count - 1;
        end else begin
            count <= count + 1;
        end
    end

endmodule