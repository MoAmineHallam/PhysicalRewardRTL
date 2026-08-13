module counter4b__base__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

always @(posedge clk, negedge rst_n) begin
    if (~rst_n) begin
        count <= 4'd0;
    end else begin
        count <= count + 1;
    end
end

endmodule