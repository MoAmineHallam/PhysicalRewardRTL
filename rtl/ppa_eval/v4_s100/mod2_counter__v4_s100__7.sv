module mod2_counter__v4_s100__7 (
    input  wire clk,
    input  wire rst_n,
    output reg  [0:0] count
);

reg [1:0] counter;

always @(posedge clk or negedge rst_n)
begin
    if (~rst_n) begin
        counter <= 2'b0;
        count <= 1'b0;
    end
    else begin
        counter <= counter + 1;
        count <= counter[0];
    end
end

endmodule