module updown12b__base__3 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [11:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 12'b0;
    end else begin
        if (dir == 1'b1) begin
            count <= count - 1;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule