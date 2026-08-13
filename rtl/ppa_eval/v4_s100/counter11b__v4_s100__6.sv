module counter11b__v4_s100__6 (
    input  wire clk,
    input  wire rst_n,
    output reg  [10:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 11'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule