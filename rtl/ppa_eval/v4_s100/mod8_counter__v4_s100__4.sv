module mod8_counter__v4_s100__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);

reg [2:0] count_next;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 3'b0;
    end else begin
        count <= count_next;
    end
end

always @(*) begin
    case (count)
        3'b000: count_next = 3'b001;
        3'b001: count_next = 3'b010;
        3'b010: count_next = 3'b011;
        3'b011: count_next = 3'b100;
        3'b100: count_next = 3'b101;
        3'b101: count_next = 3'b110;
        3'b110: count_next = 3'b111;
        3'b111: count_next = 3'b000;
    endcase
end

endmodule