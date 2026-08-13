module mod108_counter__base__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

always @(posedge clk) begin
    if (!rst_n) begin
        count <= 7'b0;
    end else begin
        if (count == 7'd107) begin
            count <= 7'b0;
        end else begin
            count <= count + 7'b1;
        end
    end
end

endmodule