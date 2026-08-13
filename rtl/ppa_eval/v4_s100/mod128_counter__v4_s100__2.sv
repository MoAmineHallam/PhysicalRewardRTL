module mod128_counter__v4_s100__2 (
    input  wire clk,
    input  wire rst_n,
    output reg  [6:0] count
);

reg [6:0] count_next;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 7'b0;
    end else begin
        count <= count_next;
    end
end

always @(*) begin
    count_next = count + 1;
end

endmodule