module mod32_counter__base__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 5'b0; // reset to 0
    end else begin
        if (count == 5'b11111) begin
            count <= 5'b0; // wrap around to 0
        end else begin
            count <= count + 1; // increment count
        end
    end
end

endmodule