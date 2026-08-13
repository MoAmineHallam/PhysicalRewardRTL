module updown10b__base__3 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [9:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 0;
    end
    else if (dir) begin
        count <= count - 1;
    end
    else begin
        count <= count + 1;
    end
end

endmodule