module mod152_counter__base__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (!rst_n) begin
        count <= 8'b0;
    end else begin
        if (count == 8'd151) begin
            count <= 8'b0;
        end else begin
            count <= count + 1;
        end
    end
end

endmodule