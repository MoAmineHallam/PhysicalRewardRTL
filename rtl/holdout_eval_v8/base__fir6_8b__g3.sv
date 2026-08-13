module base__fir6_8b__g3 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

reg [7:0] state[0:5];
reg [7:0] coeff[0:5];

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        y <= 16'd0;
        state[0] <= 8'd0;
        state[1] <= 8'd0;
        state[2] <= 8'd0;
        state[3] <= 8'd0;
        state[4] <= 8'd0;
        state[5] <= 8'd0;
        coeff[0] <= 8'd3;
        coeff[1] <= 8'd5;
        coeff[2] <= 8'd7;
        coeff[3] <= 8'd7;
        coeff[4] <= 8'd5;
        coeff[5] <= 8'd3;
    end else begin
        state[0] <= x;
        state[1] <= state[0];
        state[2] <= state[1];
        state[3] <= state[2];
        state[4] <= state[3];
        state[5] <= state[4];
        
        y <= state[0] * coeff[0] + state[1] * coeff[1] + state[2] * coeff[2] +
             state[3] * coeff[3] + state[4] * coeff[4] + state[5] * coeff[5];
    end
end

endmodule