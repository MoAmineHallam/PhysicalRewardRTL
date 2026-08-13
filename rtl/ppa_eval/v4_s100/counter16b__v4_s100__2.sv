module counter16b__v4_s100__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [15:0] count
);

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin // active-low reset
        count <= 16'b0;
    end else begin
        count <= count + 1;
    end
end

endmodule