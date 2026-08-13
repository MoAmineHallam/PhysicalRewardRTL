module updown15b__base__1 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [14:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 15'b0;
    end else begin
        if (dir == 0) begin
            count <= count + 15'b1;
        end else begin
            count <= count - 15'b1;
        end
    end
end

endmodule