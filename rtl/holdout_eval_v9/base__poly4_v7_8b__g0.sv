module base__poly4_v7_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    always @(posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= x[7:0]*(x[7:0]*(x[7:0]*(x[7:0]*24+36)+17)+21)+50;
        end
    end

endmodule