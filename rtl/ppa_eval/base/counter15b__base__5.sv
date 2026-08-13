module counter15b__base__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [14:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 0;
    end else if (count == 15'h7FFF) begin // wraps at 2^15
        count <= 0;
    end else begin
        count <= count + 1;
    end
end

endmodule