module counter6b__v4_s100__1 (
    input  wire clk,
    input  wire rst_n,
    output reg  [5:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count <= 6'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule