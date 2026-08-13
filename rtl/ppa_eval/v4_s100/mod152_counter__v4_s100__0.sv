module mod152_counter__v4_s100__0 (
    input  wire clk,
    input  wire rst_n,
    output reg  [7:0] count
);

reg [7:0] count_next;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        count <= 8'd0;
    end else begin
        count <= count_next;
    end
end

always @(*) begin
    if (count == 8'd151) begin
        count_next = 8'd0;
    end else begin
        count_next = count + 8'd1;
    end
end

endmodule