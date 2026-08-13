module mod16_counter__v4_s100__6 (
    input  wire clk,
    input  wire rst_n,
    output reg  [3:0] count
);

reg [3:0] next_count;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 4'b0000;
    end else begin
        count <= next_count;
    end
end

always @(*) begin
    next_count = count + 1;
end

endmodule