module counter14b__v4_s100__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [13:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 14'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule