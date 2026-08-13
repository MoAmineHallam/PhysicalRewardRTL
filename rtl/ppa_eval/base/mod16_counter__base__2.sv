module mod16_counter__base__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 4'b0;
    end else begin
        if (count == 4'd15) begin
            count <= 4'd0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule