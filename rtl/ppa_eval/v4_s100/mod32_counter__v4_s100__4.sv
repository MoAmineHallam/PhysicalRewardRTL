module mod32_counter__v4_s100__4 (
    input  wire clk,
    input  wire rst_n,
    output reg  [4:0] count
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
    case (count)
        5'd31: count_next = 5'd0;
        default: count_next = count + 5'd1;
    endcase
end

endmodule