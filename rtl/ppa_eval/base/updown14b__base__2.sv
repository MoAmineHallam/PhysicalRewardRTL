module updown14b__base__2 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [13:0] count
);

    always @(posedge clk, negedge rst_n) begin
        if (rst_n == 0) begin
            count <= 14'h0;
        end else begin
            if (dir == 0) begin
                count <= count + 1;
            end else begin
                count <= count - 1;
            end
        end
    end

endmodule