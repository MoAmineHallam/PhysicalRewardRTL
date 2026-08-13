module updown7b__base__0 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [6:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        count <= 7'b0;
    end else begin
        if (dir == 0) begin
            count <= count + 1;
        end else begin
            count <= count - 1;
        end
    end
end

endmodule