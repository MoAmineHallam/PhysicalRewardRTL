module mod21_counter__v4_s100__0 (
    input wire clk,
    input wire rst_n,
    output reg [4:0] count
);

reg [4:0] count_next;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 5'b0;
    end else begin
        count <= count_next;
    end
end

always @(*) begin
    count_next = count + 5'b1;
    if (count_next == 5'b10101) begin
        count_next = 5'b0;
    end
end

endmodule