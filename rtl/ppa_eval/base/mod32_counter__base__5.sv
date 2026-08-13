module mod32_counter__base__5 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 5'd0;
    end
    else begin
        if (count == 5'd31) begin
            count <= 5'd0;
        end
        else begin
            count <= count + 1;
        end
    end
end

endmodule