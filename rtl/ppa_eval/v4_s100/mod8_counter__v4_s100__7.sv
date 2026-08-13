module mod8_counter__v4_s100__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [2:0] count
);

reg [2:0] counter;

always @(posedge clk or negedge rst_n) begin
    if (~rst_n) begin
        counter <= 3'b0;
    end else begin
        counter <= counter + 1;
    end
end

assign count = counter;

endmodule