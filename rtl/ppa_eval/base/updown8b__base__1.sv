module updown8b__base__1 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else if (dir == 0) begin
        count <= count + 1;
    end else begin
        count <= count - 1;
    end
end

endmodule