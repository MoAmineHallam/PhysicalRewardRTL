module base__poly7_v3_8b__g0 (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  x,
    output reg  [15:0] y
);

    reg [15:0] poly_coeff [0:7];

    always @ (posedge clk) begin
        if (!rst_n) begin
            y <= 0;
        end else begin
            y <= poly_coeff[0] + x*(poly_coeff[1] + x*(poly_coeff[2] + x*(poly_coeff[3] + x*(poly_coeff[4] + x*(poly_coeff[5] + x*(poly_coeff[6] + x*poly_coeff[7]))))));
        end
    end

    assign poly_coeff[0] = 90;
    assign poly_coeff[1] = 50;
    assign poly_coeff[2] = 36;
    assign poly_coeff[3] = 12;
    assign poly_coeff[4] = 64;
    assign poly_coeff[5] = 89;
    assign poly_coeff[6] = 16;
    assign poly_coeff[7] = 85;

endmodule