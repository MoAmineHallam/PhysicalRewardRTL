module sft__firr6__g7 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);
    reg [7:0] xs [0:5];
    reg [15:0] PRODS [0:5];
    integer i;
    always @(posedge clk) begin
        if (!rst_n) begin
            for (i = 0; i < 6; i = i + 1) begin xs[i] <= 8'd0; PRODS[i] <= 16'd0; end
            y <= 16'd0;
        end else begin
            xs[0] <= x;
            for (i = 1; i < 6; i = i + 1) xs[i] <= xs[i-1];
            PRODS[0] <= 8'd1 * xs[0];
            PRODS[1] <= 8'd2 * xs[1];
            PRODS[2] <= 8'd3 * xs[2];
            PRODS[3] <= 8'd4 * xs[3];
            PRODS[4] <= 8'd5 * xs[4];
            PRODS[5] <= 8'd6 * xs[5];
            y <= PRODS[0] + PRODS[1] + PRODS[2] + PRODS[3] + PRODS[4] + PRODS[5];
        end
    end
endmodule