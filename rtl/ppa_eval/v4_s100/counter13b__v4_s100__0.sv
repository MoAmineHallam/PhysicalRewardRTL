module counter13b__v4_s100__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [12:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 13'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule