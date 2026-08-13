module counter10b__base__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [9:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 10'b0;
    end else begin
        if (count == 10'b1111111111) begin
            count <= 10'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule