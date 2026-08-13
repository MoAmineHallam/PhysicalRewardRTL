module updown13b__base__7 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [12:0] count
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= 13'b0;
        end else if (dir == 0) begin
            count <= count + 1;
        end else begin
            count <= count - 1;
        end
    end

endmodule