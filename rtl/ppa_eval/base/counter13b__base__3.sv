module counter13b__base__3 (
    input  wire clk,
    input  wire rst_n,
    output reg  [12:0] count
);

always @(negedge rst_n or posedge clk) begin
    if (~rst_n) begin
        count <= 13'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule