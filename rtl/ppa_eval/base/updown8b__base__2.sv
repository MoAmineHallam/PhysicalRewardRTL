module updown8b__base__2 (
    input  wire clk,
    input  wire rst_n,
    input  wire dir,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'b0; // reset count to 0
    end else begin
        if (dir == 1'b0) begin // count up
            count <= count + 1;
        end else begin // count down
            count <= count - 1;
        end
    end
end

endmodule