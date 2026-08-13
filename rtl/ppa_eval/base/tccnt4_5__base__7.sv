module tccnt4_5__base__7 (
    input  wire clk, rst_n,
    output reg  [3:0] count,
    output reg  tc
);

always @(posedge clk or negedge rst_n) begin
    if (rst_n == 1'b0) begin
        count <= 4'b0;
        tc <= 1'b0;
    end else begin
        if (count == 4'd5) begin
            count <= 4'b0;
            tc <= 1'b1;
        end else begin
            count <= count + 1;
            tc <= 1'b0;
        end
    end
end

endmodule