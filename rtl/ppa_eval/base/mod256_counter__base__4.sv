module mod256_counter__base__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'b0;
    end else begin
        if (count == 8'hff) begin
            count <= 8'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule